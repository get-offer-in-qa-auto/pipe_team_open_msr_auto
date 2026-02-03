from typing import List, Optional, Annotated, Any

from src.api.generators.generating_rule import GeneratingRule
from src.api.models.base_model import BaseModel

#TODO: Тут генерировать данные
class PersonNameRequest(BaseModel):
    # по доке: givenName, familyName :contentReference[oaicite:1]{index=1}
    givenName: Annotated[str, GeneratingRule(regex=r"^[A-Z][a-z]{2,12}$")]
    familyName: Annotated[str, GeneratingRule(regex=r"^[A-Z][a-z]{2,16}$")]


class PersonAddressRequest(BaseModel):
    # по доке (пример): address1, cityVillage, country, postalCode :contentReference[oaicite:2]{index=2}
    address1: Annotated[str, GeneratingRule(regex=r"^[A-Za-z0-9 ,.-]{5,60}$")]
    cityVillage: Annotated[str, GeneratingRule(regex=r"^[A-Za-z .-]{2,40}$")]
    country: Annotated[str, GeneratingRule(regex=r"^[A-Za-z .-]{2,40}$")]
    postalCode: Annotated[str, GeneratingRule(regex=r"^[0-9]{4,10}$")]


class CreatePersonRequest(BaseModel):
    # по доке: names[] :contentReference[oaicite:3]{index=3}
    names: List[PersonNameRequest]

    # по доке: gender "M" (в примере) :contentReference[oaicite:4]{index=4}
    gender: Annotated[str, GeneratingRule(regex=r"^(M|F|U)$")]

    # по доке (пример): birthdate "YYYY-MM-DD" :contentReference[oaicite:5]{index=5}
    birthdate: Annotated[str, GeneratingRule(regex=r"^(19|20)\d{2}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$")]

    # по доке: addresses[] :contentReference[oaicite:6]{index=6}
    addresses: List[PersonAddressRequest]

class CreatePersonInvalidRequest(BaseModel):
    # Любые значения, чтобы можно было отправлять "плохие" payload'ы
    names: Any = None
    gender: Any = None
    birthdate: Any = None
    addresses: Any = None