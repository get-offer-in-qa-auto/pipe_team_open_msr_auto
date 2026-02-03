from typing import Annotated

from src.api.generators.generating_rule import GeneratingRule
from src.api.models.base_model import BaseModel


class UpdateProfileRequest(BaseModel):
    name: Annotated[str, GeneratingRule(regex=r"^[A-Za-z]+ [A-Za-z]+$")]
