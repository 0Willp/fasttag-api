from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Dict


class Settings(BaseSettings):
    MT01_API_KEY: str
    MT01_API_SECRET: str
    MT01_API_BASE_URL: str

    MT02_API_TOKEN: str
    MT02_API_BASE_URL: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def TAG_CREDS(self) -> Dict[str, Dict[str, str]]:
        return {
            "mt01": {
                "api_key": self.MT01_API_KEY,
                "api_secret": self.MT01_API_SECRET,
                "base_url": self.MT01_API_BASE_URL
            },
            "mt02": {
                "token": self.MT02_API_TOKEN,
                "base_url": self.MT02_API_BASE_URL
            }
        }

settings = Settings()