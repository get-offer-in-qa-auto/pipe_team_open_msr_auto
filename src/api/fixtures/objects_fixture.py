import logging

import pytest

from src.api.classes.api_manager import ApiManager
from src.api.models.responses.create_patient_response import PatientCreateResponse
from src.api.models.responses.create_person_response import CreatePersonResponse
from src.api.models.responses.create_provider_response import CreateProviderResponse
from src.api.models.responses.create_user_response import CreateUserResponse


def cleanup_object(objects: list):
    api_manager = ApiManager(objects)

    delete_objects_by_uuid(api_manager, objects, PatientCreateResponse, 'delete_patient')
    delete_objects_by_uuid(api_manager, objects, CreateProviderResponse, 'delete_provider')
    delete_objects_by_uuid(api_manager, objects, CreateUserResponse, 'delete_user')
    delete_objects_by_uuid(api_manager, objects, CreatePersonResponse, 'delete_person')
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

def delete_users(api_manager: ApiManager, objects: list):
    users = [obj for obj in objects if isinstance(obj, CreateUserResponse)]
    for user in users:
        api_manager.user_steps.delete_user(user.uuid)

def delete_providers(api_manager: ApiManager, objects: list):
    providers = [obj for obj in objects if isinstance(obj, CreateProviderResponse)]
    for provider in providers:
        api_manager.user_steps.delete_provider(provider.uuid)

def delete_patients(api_manager: ApiManager, objects: list):
    patients = [obj for obj in objects if isinstance(obj, PatientCreateResponse)]
    for patient in patients:
        api_manager.user_steps.delete_patient(patient.uuid)

def delete_persons(api_manager: ApiManager, objects: list):
    persons = [obj for obj in objects if isinstance(obj, CreatePersonResponse)]
    for person in persons:
        api_manager.user_steps.delete_person(person.uuid)


def delete_objects_by_uuid(api_manager: ApiManager, objects: list, response_type: type, delete_method_name: str):
    """
    Универсальный метод удаления.
    :param response_type: Класс ответа (например, PatientCreateResponse)
    :param delete_method_name: Имя метода в user_steps (например, 'delete_patient')
    """
    target_objects = [obj for obj in objects if isinstance(obj, response_type)]
    delete_func = getattr(api_manager.user_steps, delete_method_name)

    for item in target_objects:
        delete_func(item.uuid)