from pydantic import BaseModel
from typing import Optional

class TagData(BaseModel):
    batteryLevel: Optional[int] = None  # nivel de bateria
    collectionTime: int # tempo de coleta dos dados em formato unix timestamp
    coordinate: str # coordenadas geográficas
    latitude: float # latitude extraida da coordenada
    longitude: float # longitude extraida da coordenada
    status: str # status atual da tag

class Config:
    populate_by_name = True

class ApiResponse(BaseModel):
    code: int  # código de status da resposta
    message: str  # mensagem associada à resposta
    data: list[TagData]  # array de objetos TagData

class TagPositionResponse(TagData):
    google_maps_link: str



