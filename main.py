from fastapi import FastAPI, HTTPException
from client import FindtagClientMT01, FindtagClientMT02
from models import TagPositionResponse
import os
from typing import Dict, Any

app = FastAPI(
    title="FastTag API",
    description="API to find positions of tags in text using Findtag API.",
    version="1.0.0"
)

API_KEY = "123"
API_SECRET = "" # secret para MT01

API_TOKEN = ""   # token para MT02

"""
TAG_CREDS: Dict[str, Dict[str, str]] = {
    "mt01": {
        "API_KEY": os.getenv("MT01_API_KEY", "CHAVE_MT01_DEFAULT"),
        "API_SECRET": os.getenv("MT01_API_SECRET", "SECRET_MT01_DEFAULT")
    },
    "mt02": {
        "API_KEY": os.getenv("MT02_API_KEY", "CHAVE_MT02_DEFAULT"),
        "API_SECRET": os.getenv("MT02_API_SECRET", "SECRET_MT02_DEFAULT")
    }
}

"""
"""
def get_tag_client(tag_type: str) -> FindtagApiClient:
    if tag_type not in TAG_CREDS:
        raise HTTPException(status_code=400, detail=f"Invalid tag type: {tag_type} use MT01 or MT02")
    creds = TAG_CREDS[tag_type]

    if "default" in creds["API_KEY"] or "default" in creds["API_SECRET"]:
        raise HTTPException(status_code=500, detail=f"API credentials for {tag_type} are not set properly.")

    try:
        return FindtagApiClient(creds["API_KEY"], api_secret=creds["API_SECRET"])
    except ValueError as e:
        raise HTTPException(status_code=500, detail=f"Error initializing Findtag API client: {str(e)}")
"""


findtag_client_mt01: FindtagClientMT01 | None = None
try:
    findtag_client = FindtagClientMT01(API_KEY.strip(), api_secret=API_SECRET.strip())
except ValueError as e:
    print(f"Error initializing Findtag API client: {str(e)}")



findtag_client_mt02: FindtagClientMT02 | None = None
try:
    findtag_client_mt02 = FindtagClientMT02(API_TOKEN.strip())
except ValueError as e:
    print(f"Error initializing Findtag API MT02 client: {str(e)}")


def google_maps_link(lat: float, lon: float) -> str:
    return f"http://maps.google.com/?q={lat},{lon}"



@app.get("/tag/position/{public_key}", response_model=TagPositionResponse, summary="Get Tag Position and Google Maps Link")
async def get_tag_position_mt01(public_key: str):
    if not findtag_client:
        raise HTTPException(status_code=500, detail="Findtag API client is not initialized.")
    try:
        tag_data = findtag_client.get_device_data(public_key=public_key)
        google_maps_url = google_maps_link(tag_data.latitude, tag_data.longitude)
        return TagPositionResponse(**tag_data.model_dump(), google_maps_url=google_maps_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tag/position/mt02/{public_key}", response_model=TagPositionResponse, summary="Get Tag Position and Google Maps Link for MT02")
async def get_tag_position_mt02(public_key: str):
    if not findtag_client_mt02:
        raise HTTPException(status_code=503, detail="Findtag API MT02 client is not initialized.")

    try:
        data = findtag_client_mt02.get_device_data(public_key)
        return TagPositionResponse(**data.model_dump(),google_maps_link=google_maps_link(data.latitude, data.longitude))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))