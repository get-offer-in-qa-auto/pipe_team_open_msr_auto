from typing import Annotated

from src.api.generators.generating_rule import GeneratingRule
from src.api.models.base_model import BaseModel


class CreatePersonUi(BaseModel):
    given: Annotated[str, GeneratingRule(regex=r"^[A-Z][a-z]{2,12}$")]
    family: Annotated[str, GeneratingRule(regex=r"^[A-Z][a-z]{2,16}$")]

    # PatientCreatePage.fill_basic_info ожидает строки "male/female/unknown"
    gender: Annotated[str, GeneratingRule(regex=r"^(male|female|unknown)$")]

    # возраст (UI вводит строкой, но тебе удобно держать int)
    age: Annotated[int, GeneratingRule(regex=r"^(?:[1-9]|[1-8]\d|90)$")]  # 1..90