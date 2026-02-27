from dataclasses import dataclass
from typing import Optional

from src.api.classes.api_manager import ApiManager

@dataclass
class ApiFlow:
    api_manager: ApiManager
    patient_uuid: Optional[str] = None

    def with_patient(self, patient_uuid: str) -> "ApiFlow":
        self.patient_uuid = patient_uuid
        return self

    def get_person_full(self):
        if not self.patient_uuid:
            raise AssertionError("patient_uuid is not set")
        return self.api_manager.user_steps.get_person_full(self.patient_uuid)