from fastapi import FastAPI, HTTPException
from client import FindtagClientMT01, FindtagClientBrGPS, FindtagClientWebTag
from models import TagPositionResponse, TagData
from typing import List
from settings import settings

app = FastAPI(
    title="FastTag API",
    description="API used to authenticate with other APIs and retrieve tag positions.",
    version="2.0.0"
)

findtag_client_mt01 = None
findtag_client_brgps = None
findtag_client_webtag = None

try:
    findtag_client_mt01 = FindtagClientMT01(
        api_key=settings.MT01_API_KEY,
        api_secret=settings.MT01_API_SECRET,
        base_url=settings.MT01_API_BASE_URL
    )

    findtag_client_brgps = FindtagClientBrGPS(
       api_token=settings.BRGPS_API_TOKEN,
       base_url=settings.BRGPS_API_BASE_URL
    )

    findtag_client_webtag = FindtagClientWebTag(
        username=settings.WEBTAG_USERNAME,
        password=settings.WEBTAG_PASSWORD,
        base_url=settings.WEBTAG_BASE_URL
    )
    findtag_client_webtag.login()
except Exception as e:
    print(f"Erro ao inicializar: {e}")

def google_maps_link(lat: float, lon: float) -> str:
    return f"https://www.google.com/maps?q={lat},{lon}"

# ---MT01 ---
@app.get("/tag/position/mt01/{public_key}", response_model=TagPositionResponse, tags=["Findtag"], summary="Get Tag Position and Google Maps Link for MT01")
async def get_tag_mt01(public_key: str):
    if not findtag_client_mt01:
        raise HTTPException(status_code=503, detail="Findtag API MT01 client is not initialized.")
    try:
        data = findtag_client_mt01.get_device_data(public_key)
        return TagPositionResponse(**data.model_dump(), google_maps_link=google_maps_link(data.latitude, data.longitude))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- BrGPS ---
@app.get("/tag/position/brgps/{public_key}", response_model=TagPositionResponse, tags=["BrGPS"], summary="Get Tag Position and Google Maps Link for BrGPS")
async def get_tag_position_brgps(public_key: str):
    if not findtag_client_brgps:
        raise HTTPException(status_code=503, detail="Findtag API BrGPS client is not initialized.")
    try:
        data = findtag_client_brgps.get_device_data(public_key)
        return TagPositionResponse(**data.model_dump(),google_maps_link=google_maps_link(data.latitude, data.longitude))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/tag/brgps/all", response_model=List[int], tags=["BrGPS"], summary="Get All BrGPS Device IDs")
async def get_all_brgps():
    if not findtag_client_brgps:
        raise HTTPException(status_code=503, detail="Findtag API BrGPS client is not initialized.")

    devices = findtag_client_brgps.fetch_all_devices()
    return devices

# --- WebTag ---
@app.get("/tag/position/webtag/{public_key}", response_model=TagPositionResponse, tags=["WebTag"], summary="Get Tag Position for WebTag")
async def get_tag_position_webtag(public_key: str):
    if not findtag_client_webtag.token:
        findtag_client_webtag.login()

    try:
        data = findtag_client_webtag.get_device_data(public_key)
        return TagPositionResponse(**data.model_dump(),google_maps_link=google_maps_link(data.latitude, data.longitude))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



