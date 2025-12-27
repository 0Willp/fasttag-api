import time
import hashlib
import uuid
import random
import requests
from urllib.parse import urlencode
from typing import Dict, Any, List
from models import TagData, ApiResponse
import settings



class FindtagClientMT01:
    def __init__(self, api_key: str, api_secret: str, base_url: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url

    def _generate_signature(self, params: dict) -> str:
        sorted_keys = sorted(params.keys())
        key_value_string = "&".join([f"{k}={params[k]}" for k in sorted_keys])
        string_to_sign = f"apikey={self.api_key}&apisecret={self.api_secret}&{key_value_string}"
        return hashlib.md5(string_to_sign.encode()).hexdigest().upper()

    def get_device_data(self, public_key: str, time_period: str = '0'):
        timestamp = str(int(time.time()))
        nonce = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=8))

        request_params: Dict[str, str] = {
            'timestamp': timestamp,
            'nonce': nonce,
            'publickey': public_key,
            'timePeriod': time_period,
        }

        sign = self._generate_signature(request_params)

        full_params = {**request_params, 'apikey': self.api_key, 'sign': sign}
        url = f"{self.base_url}?{urlencode(full_params)}"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            response_body = response.json()

            if response_body.get('code') != 0:
                raise Exception(f"Error processing MT01 data: {response_body.get('msg')}")

            if response_body.get('data'):
                tag_data = response_body['data'][0]
                lon, lat = tag_data['coordinate'].split(',')
                tag_data['latitude'] = float(lat)
                tag_data['longitude'] = float(lon)
                return tag_data
        except Exception as e:
            raise Exception(f"Error processing MT01 data: {e}")

class FindtagClientMT02:
    def __init__(self, api_token: str, base_url: str):
        self.api_token = api_token
        self.base_url = base_url

    def _get_headers(self) -> Dict[str, str]:
        return {
            'api_token': self.api_token,
            'timestamp': str(int(time.time())),
            'accept': 'application/json'
        }

    def fetch_all_devices(self) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/tag/all"
        params = {"isActived": True}
        all_devices = []
        current_page = 1

        try:
            while True:
                params["page"] = current_page
                response = requests.get(url, params=params, headers=self._get_headers(), timeout=15)
                response.raise_for_status()
                page_data = response.json()
                devices = page_data.get("data", [])
                if not devices:
                    break

                all_devices.extend(devices)
                current_page += 1

            return all_devices
        except Exception as e:
            print(f"Error fetching all devices: {e}")
            return []

    def get_device_data(self, public_key: str) -> TagData:
        endpoint = f"{self.base_url}/tag"
        params = {'ids': public_key}
        #endpoint = f"{self.base_url.rstrip('/')}/tag"
        #params = {'ids': public_key.strip()}

        response = requests.get(endpoint, headers=self._get_headers(), params=params, timeout=10)

        if response.status_code == 400:
            raise Exception("Invalid public key")

        response.raise_for_status()
        data = response.json()

        target_data = None
        if isinstance(data, list) and len(data) > 0:
            target_data = data[0]
        elif isinstance(data, dict):
            if 'data' in data and isinstance(data['data'], list) and len(data['data']) > 0:
                target_data = data['data'][0]
            elif 'all' in data:
                target_data = data

        if target_data:
            return self._parse_tag_dto(target_data)

        raise Exception(f"Tag not found: {public_key}")

    def _parse_tag_dto(self, dto: Dict[str, Any]) -> TagData:
        lat, lng = float(dto.get('lat', 0)), float(dto.get('lng', 0))
        return TagData(
            batteryLevel=dto.get('battery'),
            collectionTime=dto.get('timestamp', int(time.time())),
            coordinate=f"{lng},{lat}",
            latitude=lat,
            longitude=lng,
            status="active" if dto.get('isActived') else "inactive"
        )


