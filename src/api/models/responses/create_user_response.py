from typing import List

from src.api.models.base_model import BaseModel


class Role(BaseModel):
    uuid: str
    display: str


class Person(BaseModel):
    uuid: str
    display: str


class CreateUserResponse(BaseModel):
    uuid: str
    display: str
    username: str
    systemId: str
    person: Person
    roles: List[Role]
