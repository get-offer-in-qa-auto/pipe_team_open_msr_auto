import logging

import pytest

from src.api.classes.api_manager import ApiManager
from src.api.models.responses.create_patient_response import PatientCreateResponse
from src.api.models.responses.create_person_response import CreatePersonResponse
from src.api.models.responses.create_provider_response import CreateProviderResponse
from src.api.models.responses.create_user_response import CreateUserResponse


def cleanup_object(objects: list):
    api_manager = ApiManager(objects)

    cleanup_tasks = [
        (PatientCreateResponse, 'delete_patient'),
        (CreateProviderResponse, 'delete_provider'),
        (CreateUserResponse, 'delete_user'),
        (CreatePersonResponse, 'delete_person')
    ]
    for resp_class, method_name in cleanup_tasks:
        delete_objects_by_uuid(api_manager, objects, resp_class, method_name)
    # for obj in objects:
    #     if isinstance(obj, CreatePersonResponse):
    #         api_manager.admin_steps.delete_person(obj.uuid)
    #     elif isinstance(obj, PatientCreateResponse):
    #         api_manager.admin_steps.delete_patient(obj.uuid)
    #     else:
    #         logging.warning(f'Object type: {type(obj)} is not deleted')


@pytest.fixture
def created_objects():
    objects: list = []
    yield objects
    cleanup_object(objects)

def delete_objects_by_uuid(api_manager: ApiManager, objects: list, response_type: type, delete_method_name: str):
    """
        Универсальный метод удаления cущностей
    """
    target_objects = [obj for obj in objects if isinstance(obj, response_type)]
    delete_func = getattr(api_manager.user_steps, delete_method_name)

    for item in target_objects:
        delete_func(item.uuid)