from src.api.models.base_model import BaseModel


class CreateProviderRequest(BaseModel):
    person: str
    identifier: str
    retired: bool