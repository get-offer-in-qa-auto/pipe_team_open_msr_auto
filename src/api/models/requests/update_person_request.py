from typing import Optional

from src.api.models.base_model import BaseModel


class UpdatePersonRequest(BaseModel):
    # partial update: передаём только то, что хотим изменить
    gender: Optional[str] = None  # "M" | "F" | "U"
    birthdate: Optional[str] = None  # "YYYY-MM-DD"