from src.api.models.base_model import BaseModel


class CreateProviderPersonModel(BaseModel):
    uuid: str
    display: str


class CreateProviderResponse(BaseModel):
    uuid: str
    display: str
    person: CreateProviderPersonModel
    retired: bool
