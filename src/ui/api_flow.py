import allure
from dataclasses import dataclass
from typing import Optional, Callable

from src.api.classes.api_manager import ApiManager
from src.api.models.responses.create_patient_response import PatientCreateResponse


@dataclass
class ApiFlow:
    api_manager: ApiManager
    patient_uuid: Optional[str] = None

    @allure.step("with_patient")
    def with_patient(self, patient_uuid: str) -> "ApiFlow":
        self.patient_uuid = patient_uuid
        return self

    @allure.step("register_created_patient")
    def register_created_patient(self, created_objects: list) -> "ApiFlow":
        """
        Добавляет PatientCreateResponse(uuid=patient_uuid) в created_objects
        чтобы teardown удалил пациента.
        """
        if not self.patient_uuid:
            raise AssertionError("patient_uuid is not set")
        created_objects.append(PatientCreateResponse(uuid=self.patient_uuid))
        return self

    @allure.step("call_api")
    def call_api(self, api_method: Callable):
        """
        Вызов любого API-метода с текущим patient_uuid.

        Пример:
            .call_api(api_manager.user_steps.get_person_full)
        """
        if not self.patient_uuid:
            raise AssertionError("patient_uuid is not set")

        return api_method(self.patient_uuid)