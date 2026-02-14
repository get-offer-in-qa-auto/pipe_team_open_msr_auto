from src.api.models.base_model import BaseModel


class PatientContext(BaseModel):
    patient_uuid: str
    location_uuid: str