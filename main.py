from fastapi import FastAPI, HTTPException
from settings import settings
from client import FindtagClientMT01, FindtagClientMT02
from models import TagPositionResponse, TagData
from typing import List

app = FastAPI(
    title="FastTag API",
    description="API to find positions of tags in text using Findtag API.",
    version="1.0.0"
)

'''
try:
    creds_mt01 = settings.TAG_CREDS["mt01"]
    findtag_client = FindtagClientMT01(
        api_key=creds_mt01["api_key"],
        api_secret=creds_mt01["api_secret"],
        base_url=creds_mt01["base_url"]
    )

    creds_mt02 = settings.TAG_CREDS["mt02"]
    findtag_client_mt02 = FindtagClientMT02(
        api_token=creds_mt02["token"],
        base_url=creds_mt02["base_url"]
    ) 
except Exception as e:
    print(f"Critical Error initializing clients: {e}")
    '''

findtag_client_mt02: FindtagClientMT02 | None = None
try:
    creds_mt02 = settings.TAG_CREDS["mt02"]
    findtag_client_mt02 = FindtagClientMT02(
        api_token=creds_mt02["token"],
        base_url=creds_mt02["base_url"]
    )
except Exception as e:
    print(f"Critical Error initializing clients: {e}")

def google_maps_link(lat: float, lon: float) -> str:
    return f"https://www.google.com/maps?q={lat},{lon}"

# --- ENDPOINTS MT01 ---
@app.get("/tag/position/mt01/{public_key}", response_model=TagPositionResponse)
async def get_tag_mt01(public_key: str):
    try:
        data = client_mt01.get_device_data(public_key)
        return TagPositionResponse(
            **data,
            google_maps_link=google_maps_link(data['latitude'], data['longitude'])
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



# --- ENDPOINTS MT02 ---
@app.get("/tag/position/mt02/{public_key}", response_model=TagPositionResponse, summary="Get Tag Position and Google Maps Link for MT02")
async def get_tag_position_mt02(public_key: str):
    if not findtag_client_mt02:
        raise HTTPException(status_code=503, detail="Findtag API MT02 client is not initialized.")
    try:
        data = findtag_client_mt02.get_device_data(public_key)
        return TagPositionResponse(**data.model_dump(),google_maps_link=google_maps_link(data.latitude, data.longitude))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/tag/mt02/all", response_model=List[TagData], summary="List all active MT02 tags")
async def get_all_mt02():
    devices = findtag_client_mt02.fetch_all_devices()
    if not devices:
        return []
    return [findtag_client_mt02._parse_tag_dto(d) for d in devices]






