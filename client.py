import time
import hashlib
import random
import requests
from urllib.parse import urlencode
from typing import Dict, Any, List
from models import TagData, ApiResponse


API_URL_MT01 = 'https://server.findtag.top/fit/openapi/devicedata/v1'
API_URL_MT02 = 'http://www.brgps.com/open'

class FindtagClientMT01:
    def __init__(self, api_key: str, api_secret: str):
        if not api_key or not api_secret:
            raise Exception('API key and secret are required.')
        self.api_key = api_key
        self.api_secret = api_secret

    def _generate_signature(self, params: dict) -> str:
        sorted_keys = sorted(params.keys())
        key_value_string = '&'.join(f"{key}={params[key]}" for key in sorted_keys)
        string_to_sign = f"apikey={self.api_key}&apisecret={self.api_secret}&{key_value_string}"
        md5_hash = hashlib.md5(string_to_sign.encode('utf-8')).hexdigest()
        return md5_hash.upper()

    def get_device_data(self, public_key: str, time_period: str = '0') -> 'TagData':
        timestamp = str(int(time.time()))
        nonce = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=8))

        request_params: Dict[str, str] = {
            'timestamp': timestamp,
            'nonce': nonce,
            'publickey': public_key,
            'timePeriod': time_period,
        }

        sign = self._generate_signature(request_params)

        full_params = request_params.copy()
        full_params['apikey'] = self.api_key
        full_params['sign'] = sign

        url = f"{API_URL_MT01}?{urlencode(full_params)}"

        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error fetching data from Findtag API: {e}") from e

        try:
            response_data = response.json()
            response_body = ApiResponse(**response_data)
        except Exception:
            raise Exception(f"Error parsing response from Findtag API: {response.text}")

        if response_body.code != 0:
            raise Exception(f"Error fetching data from Findtag API: {response_body.code}")

        if response_body.data:
            tag_data = response_body.data[0]

            longitude_str, latitude_str = tag_data.coordinate.split(',')

            tag_data.latitude = float(latitude_str)
            tag_data.longitude = float(longitude_str)

            return tag_data

        raise Exception("No data found.")


class FindtagClientMT02:
    def __init__(self, api_token: str):
        if not api_token:
            raise ValueError('API key required.')
        self.api_token = api_token

    def _get_headers(self) -> Dict[str, str]:
        return {
            'api_token': self.api_token,
            'timestamp': str(int(time.time())),
            'Content-Type': 'application/json'
        }

    def get_device_data(self, public_key: str) -> TagData:
        endpoint = f"{API_URL_MT02}/tag"
        params = {'ids': public_key}

        try:
            response = requests.get(endpoint, headers=self._get_headers(), params=params, timeout=10)
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

            raise Exception(f"Tag not found or empty response: {data}")

        except requests.exceptions.RequestException as e:
            raise Exception(f"Error processing MT02 data: {e}")
        except Exception as e:
            raise Exception(f": {e}")

    def _parse_tag_dto(self, dto: Dict[str, Any]) -> TagData:
        try:
            latitude = float(dto.get('lat', 0))
            longitude = float(dto.get('lng', 0))

            return TagData(
                batteryLevel=dto.get('battery'),
                collectionTime=dto.get('timestamp'),
                coordinate=f"{longitude},{latitude}",
                latitude=latitude,
                longitude=longitude,
                status="active" if dto.get('isActived') else "inactive"
            )
        except (ValueError, TypeError) as e:
            raise Exception(f"Error converting Tag data format: {e}")


