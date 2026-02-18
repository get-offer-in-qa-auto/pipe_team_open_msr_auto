from typing import List

from src.api.models.requests.base_create_user_request import BaseCreateUserRequest


class CreateUserFromExistingPersonRequest(BaseCreateUserRequest):
    person: str # uuid существующей Person
    roles: List[str]
