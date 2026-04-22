import time
import hashlib
import uuid
import random
import requests
from urllib.parse import urlencode
from typing import Dict, Any, List
from datetime import datetime
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

class FindtagClientBrGPS:
    def __init__(self, api_token: str, base_url: str):
        self.api_token = api_token.strip()
        self.base_url = base_url.strip().rstrip('/')

    def _get_headers(self) -> Dict[str, str]:
        return {
            'api_token': self.api_token,
            'timestamp': str(int(time.time())),
            'Content-Type': 'application/json'
        }

    def fetch_all_devices(self) -> List[Dict[str, Any]]:
        endpoint = f"{self.base_url}/tag/all"
        params = {"isActived": True}
        all_devices = []
        current_page = 1

        try:
            while True:
                params["page"] = current_page
                response = requests.get(endpoint, params=params, headers=self._get_headers(), timeout=15)
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
            return all_devices

    def get_device_data(self, public_key: str) -> TagData:
        endpoint = f"{self.base_url}/tag"
        params = {'ids': public_key.strip()}

        response = requests.get(endpoint, headers=self._get_headers(), params=params, timeout=10)

        if response.status_code == 400:
            raise Exception("Error fetching tag data, check your API token and url API.")

        response.raise_for_status()
        data = response.json()

        target_data = data[0] if isinstance(data, list) and data else data.get('data', [None])[0]
        if not target_data:
            raise Exception(f"Tag not found: {public_key}")

        return self._parse_tag_dto(target_data)

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


class FindtagClientWebTag:
    def __init__(self, developer_id: int, base_url:str):
        self.developer_id = developer_id
        self.base_url = base_url.strip().rstrip('/')

    """
    def login(self):
        url = "https://liketop.webtag.com.br/api/interface/login"
        headers = headers = {"language": "en","Content-Type": "application/json"}
        payload = {"username": self.username, "password": self.password}
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        data = response.json()
        if data.get('code') == "00000":
            self.developer_id = data.get("id")
            self.token = data.get("token")
            return
        raise Exception(f"Erro login WebTag: {data.get('msg')}")
    """

    def get_device_data(self, public_key: str) -> TagData:
        # Request path: /interface/v3/device/:uid
        endpoint = f"{self.base_url}/interface/v3/device/{self.developer_id}"
        headers = {"la": "pt","Content-Type": "application/json"}

        payload = {"sn": str(public_key)}

        try:
            response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            response_data = response.json()

            if response_data.get("code") == "200" or response_data.get("msg") == "sucess":
                data_obj = response_data.get("data", {})
                trajectory_list = data_obj.get("trajectory", [])

                if trajectory_list:
                    latest_trajectory = trajectory_list[-1]

                    return self._parse_webtag_v3(latest_trajectory)

                raise Exception(f"No trajectory found for the equipment.: {public_key}")

            raise Exception(f"Erro WebTag ({response_data.get('code')}): {response_data.get('msg')}")

        except requests.exceptions.RequestException as e:
            raise Exception(f"Error retrieving data from WebTag: {e}")


    def _parse_webtag_v3(self, item: dict) -> TagData:
        battery_level = int(item.get("status", 0))
        if battery_level <= 32:battery = 100  # Full
        elif battery_level <= 96:battery = 60  # Medium
        elif battery_level <= 160:battery = 20  # Low
        else:battery = 10  # Critical

        return TagData(
            batteryLevel=battery,
            collectionTime=int(item.get("timestamp", time.time() * 1000) / 1000),
            coordinate=f"{item['longitude']},{item['latitude']}",
            latitude=float(item['latitude']),
            longitude=float(item['longitude']),
            status="active"
        )


class FindtagClientNanoTag:
    def __init__(self, api_token: str, base_url:str):
        self.api_token = api_token.strip()
        self.base_url = base_url.strip()

    def get_device_data(self, public_key: str) -> TagData:
        payload = {
            "token": self.api_token,
            "requisicao": "last_position"
        }

        response = requests.post(self.base_url, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data.get("success"):
            raise Exception(f"Error fetching tag data, check your API token and url API.")

        devices = data.get("data", [])
        target_device = next((d for d in devices if d.get("id") == public_key), None)

        if not target_device:
            raise Exception(f"Tag not found: {public_key}")

        return self._parse_tag_dto(target_device)

    def _parse_tag_dto(self, dto: Dict[str, Any]) -> TagData:
        lat = float(dto.get('lat', 0))
        lng = float(dto.get('lng', 0))

        data_string = dto.get('datahora', "")
        timestamp = int(time.time())
        if data_string:
            try:
                dt_obj = datetime.strptime(data_string, "%d/%m/%Y %H:%M:%S")
                timestamp = int(dt_obj.timestamp())
            except ValueError:
                pass

        return TagData(
            batteryLevel=int(dto.get('bat', 0)),
            collectionTime=timestamp,
            coordinate=f"{lng},{lat}",
            latitude=lat,
            longitude=lng,
            status="active"
        )