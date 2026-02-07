from typing import List

from src.api.models.requests.BaseCreateUserRequest import BaseCreateUserRequest


class CreateUserFromExistingPersonRequest(BaseCreateUserRequest):
    person: str # uuid существующей Person
    roles: List[str]
