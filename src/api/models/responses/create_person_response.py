from typing import List, Optional, Any
from src.api.models.base_model import BaseModel

#TODO: понять с full
class Link(BaseModel):
    rel: str
    uri: str
    resourceAlias: Optional[str] = None


class PreferredName(BaseModel):
    uuid: str
    display: Optional[str] = None
    links: Optional[List[Link]] = None


class CreatPersonResponse(BaseModel):
    uuid: str
    display: str
    gender: str
    voided: bool
    preferredName: PreferredName
    links: List[Link]
    resourceVersion: Optional[str] = None


# Для v=full удобнее взять “мягкую” модель (т.к. полей много и они могут отличаться)
class PersonFullResponse(BaseModel):
    uuid: str
    display: str
    gender: str
    voided: bool

    # поля, которые точно встречаются в full
    names: List[Any]
    attributes: List[Any]
    birthdateEstimated: bool
    dead: bool
    deathdateEstimated: bool

    preferredName: Any
    links: List[Link]
