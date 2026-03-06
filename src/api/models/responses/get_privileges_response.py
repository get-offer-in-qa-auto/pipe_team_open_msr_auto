from typing import List

from src.api.models.base_model import BaseModel


class GetPrivilegesModel(BaseModel):
    uuid: str
    display: str
    name: str
    description: str


class GetPrivilegesResponse(BaseModel):
    results: List[GetPrivilegesModel]
