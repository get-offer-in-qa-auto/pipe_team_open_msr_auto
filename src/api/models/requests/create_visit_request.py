from typing import List, Optional

from src.api.models.base_model import BaseModel


class CreateVisitRequest(BaseModel):
    """Payload for POST /visit.

    Docs: https://rest.openmrs.org/#create-visit
    """

    patient: str
    visitType: str
    startDatetime: str
    location: str
    indication: Optional[str] = None
    encounters: Optional[List[str]] = None