from typing import List, Optional
from src.api.models.base_model import BaseModel


class LocationLink(BaseModel):
    rel: str
    uri: str
    resourceAlias: Optional[str]


class LocationResult(BaseModel):
    uuid: str
    display: str
    links: List[LocationLink]


class LocationListLink(BaseModel):
    rel: str
    uri: str
    resourceAlias: Optional[str]


class LocationListResponse(BaseModel):
    results: List[LocationResult]
    links: Optional[List[LocationListLink]] = None
