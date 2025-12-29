from fastapi import FastAPI, HTTPException
from client import FindtagClientMT01, FindtagClientMT02
from models import TagPositionResponse, TagData
from typing import List
from settings import settings

app = FastAPI(
    title="FastTag API",
    description="API used to authenticate with other APIs and retrieve tag positions.",
    version="2.0.0"
)

findtag_client_mt01 = None
findtag_client_mt02 = None

try:
    findtag_client_mt01 = FindtagClientMT01(
        api_key=settings.MT01_API_KEY,
        api_secret=settings.MT01_API_SECRET,
        base_url=settings.MT01_API_BASE_URL
    )

    findtag_client_mt02 = FindtagClientMT02(
       api_token=settings.MT02_API_TOKEN,
       base_url=settings.MT02_API_BASE_URL
    )
except Exception as e:
    print(f"Erro ao inicializar: {e}")

def google_maps_link(lat: float, lon: float) -> str:
    return f"https://www.google.com/maps?q={lat},{lon}"

# --- ENDPOINTS MT01 ---
@app.get("/tag/position/mt01/{public_key}", response_model=TagPositionResponse, tags=["MT01 (Findtag)"], summary="Get Tag Position and Google Maps Link for MT01")
async def get_tag_mt01(public_key: str):
    if not findtag_client_mt01:
        raise HTTPException(status_code=503, detail="Findtag API MT01 client is not initialized.")
    try:
        data = findtag_client_mt01.get_device_data(public_key)
        return TagPositionResponse(**data.model_dump(), google_maps_link=google_maps_link(data.latitude, data.longitude))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- ENDPOINTS MT02 ---
@app.get("/tag/position/mt02/{public_key}", response_model=TagPositionResponse, tags=["MT02 (BrGPS)"], summary="Get Tag Position and Google Maps Link for MT02")
async def get_tag_position_mt02(public_key: str):
    if not findtag_client_mt02:
        raise HTTPException(status_code=503, detail="Findtag API MT02 client is not initialized.")
    try:
        data = findtag_client_mt02.get_device_data(public_key)
        return TagPositionResponse(**data.model_dump(),google_maps_link=google_maps_link(data.latitude, data.longitude))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/tag/mt02/all", response_model=List[int], tags=["MT02 (BrGPS)"], summary="Get All MT02 Device IDs")
async def get_all_mt02():
    if not findtag_client_mt02:
        raise HTTPException(status_code=503, detail="Findtag API MT02 client is not initialized.")

    devices = findtag_client_mt02.fetch_all_devices()
    return devices





