import pytest

from src.api.classes.api_manager import ApiManager
from src.api.models.responses.create_patient_response import PatientCreateResponse
from src.api.models.responses.create_person_response import CreatePersonResponse
from src.api.models.responses.create_provider_response import CreateProviderResponse
from src.api.models.responses.create_role_response import CreateRoleResponse
from src.api.models.responses.create_user_response import CreateUserResponse


def cleanup_object(objects: list):
    api_manager = ApiManager(objects)

    patients = [o for o in objects if isinstance(o, PatientCreateResponse)]
    for p in patients:
        try:
            person = api_manager.database_steps.get_person_by_uuid(p.uuid)
            patient_id = person.person_id

            visits = api_manager.database_steps.get_visits_by_patient_id(patient_id)
            for v in visits:
                api_manager.visit_steps.delete_visit(v.uuid, purge=True)
        except Exception:
            pass

    cleanup_tasks = [
        (PatientCreateResponse, "delete_patient"),
        (CreateProviderResponse, "delete_provider"),
        (CreateUserResponse, "delete_user"),
        (CreatePersonResponse, "delete_person"),
        (CreateRoleResponse, "delete_role"),
    ]
    for resp_class, method_name in cleanup_tasks:
        delete_objects_by_uuid(api_manager, objects, resp_class, method_name)


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