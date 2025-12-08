import time
import hashlib
import random
import requests
from urllib.parse import urlencode

from deploy import response

API_URL = 'https://server.findtaq.top/fit/openapi/devicedata/v1'

class FindtagApiClient:
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

    def get_device_data(self, public_key: str, time_period: str = '0') -> TagData:
        timestamp = str(int(time.time()))
        nonce = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=8))

        request_params = {
            'timestamp': timestamp,
            'nonce': nonce,
            'publickey': public_key,
            'timePeriod': time_period,
        }

        sign = self._generate_signature(request_params)

        full_params = request_params.copy()
        full_params['apikey'] = self.api_key
        full_params['sign'] = sign

        url = f"{API_URL}?{urlencode(full_params)}"

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

