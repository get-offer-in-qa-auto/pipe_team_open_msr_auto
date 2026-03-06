from typing import List

from src.api.models.base_model import BaseModel


class CreateRolePrivilegeModel(BaseModel):
    name: str
    description: str


class CreateRoleRequest(BaseModel):
    name: str
    description: str
    privileges: List[CreateRolePrivilegeModel]
