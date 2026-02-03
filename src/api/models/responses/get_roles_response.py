from typing import List
from src.api.models.base_model import BaseModel


class RoleLink(BaseModel):
    rel: str
    uri: str
    resourceAlias: str


class RoleResult(BaseModel):
    uuid: str
    display: str
    links: List[RoleLink]


class RoleListResponse(BaseModel):
    results: List[RoleResult]
