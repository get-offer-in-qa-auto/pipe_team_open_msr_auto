import logging

import pytest

from src.api.classes.api_manager import ApiManager
from src.api.models.responses.create_patient_response import PatientCreateResponse
from src.api.models.responses.create_person_response import CreatPersonResponse
from src.api.models.responses.create_visit_response import VisitCreateResponse


def cleanup_object(objects: list):
    api_manager = ApiManager(objects)
    for obj in reversed(objects):
        if isinstance(obj, VisitCreateResponse):
            api_manager.visit_steps.delete_visit(obj.uuid, purge=True)
        elif isinstance(obj, PatientCreateResponse):
            api_manager.admin_steps.delete_patient(obj.uuid, purge=True)
        elif isinstance(obj, CreatPersonResponse):
            api_manager.admin_steps.delete_person(obj.uuid, purge=True)
        else:
            logging.warning(f'Object type: {type(obj)} is not deleted')


@pytest.fixture
def created_objects():
    objects: list = []
    yield objects
    cleanup_object(objects)