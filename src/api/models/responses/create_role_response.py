from src.api.models.base_model import BaseModel


class CreateRoleResponse(BaseModel):
    uuid: str
    display: str
    name: str
    description: str