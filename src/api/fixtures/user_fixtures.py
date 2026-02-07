from typing import Optional, List

import pytest

from src.api.classes.api_manager import ApiManager
from src.api.generators.random_model_generator import RandomModelGenerator
from src.api.models.requests.create_person_request import CreatePersonRequest
from src.api.models.requests.create_user_from_existing_person_request import CreateUserFromExistingPersonRequest
from src.api.models.responses.create_person_response import CreatePersonResponse
from src.api.models.responses.create_user_response import CreateUserResponse


@pytest.fixture
def create_user_with_roles(api_manager: ApiManager):
    """
        Фикстура для создания пользователя с заданными правами.
        По умолчанию создает пользователя с ролью ["Privilege Level: Full"]
    """

    def _create_user(roles: Optional[List[str]] = None):
        create_person_request: CreatePersonRequest = RandomModelGenerator.generate(CreatePersonRequest)
        person_data: CreatePersonResponse = api_manager.user_steps.create_person(create_person_request)

        if roles is None:
            roles = ["Privilege Level: Full"]

        roles_uuids = [role_info.uuid for role_info in api_manager.user_steps.get_roles().results if role_info.display in roles]

        return _create_user_with_roles(api_manager, person_data.uuid, roles_uuids)

    return _create_user

@pytest.fixture
def create_user_with_privileges(api_manager: ApiManager):
    """
        Фикстура для создания пользователя с заданными привилегиями.
        По умолчанию создает пользователя со всеми привилегиями
    """

    def _create_user(exclude_privilege_names: Optional[List[str]] = None):
        create_person_request: CreatePersonRequest = RandomModelGenerator.generate(CreatePersonRequest)
        person_data: CreatePersonResponse = api_manager.user_steps.create_person(create_person_request)

        create_role_response = api_manager.user_steps.create_role_with_excluded_privileges(exclude_privilege_names)
        roles_uuids = [create_role_response.uuid]

        return _create_user_with_roles(api_manager, person_data.uuid, roles_uuids)


    return _create_user

@pytest.fixture
def created_person(api_manager: ApiManager):
    return api_manager.user_steps.create_person(RandomModelGenerator.generate(CreatePersonRequest))

def _create_user_with_roles(api_manager: ApiManager, person_uuid: str, roles: List[str]):
    create_user_request: Optional[CreateUserFromExistingPersonRequest] = RandomModelGenerator.generate(
        CreateUserFromExistingPersonRequest)
    create_user_request.person = person_uuid
    create_user_request.roles = roles
    user_data: CreateUserResponse = api_manager.user_steps.create_user_from_existing_person(create_user_request)
    return create_user_request, user_data