from typing import Annotated

from src.api.generators.generating_rule import GeneratingRule
from src.api.models.base_model import BaseModel


class BaseCreateUserRequest(BaseModel):
    username: Annotated[str, GeneratingRule(regex=r"^[A-Za-z0-9]{3,15}$")]
    password: Annotated[str, GeneratingRule(regex=r"^[A-Z]{3}[a-z]{4}[0-9]{3}$")]
    systemId: str = "systemId"