from src.api.models.base_model import BaseModel


class UpdateVisitRequest(BaseModel):
    stopDatetime: str | None = None
