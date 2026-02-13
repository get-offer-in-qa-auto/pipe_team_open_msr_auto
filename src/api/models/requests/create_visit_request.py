from typing import List, Optional, Any

from src.api.models.base_model import BaseModel


class CreateVisitRequest(BaseModel):
    """Payload for POST /visit.

    Docs: https://rest.openmrs.org/#create-visit
    """

    patient: str
    visitType: str
    startDatetime: str
    stopDatetime: Optional[str] = None
    location: str
    indication: Optional[str] = None
    encounters: Optional[List[str]] = None


class CreateVisitInvalidRequest(BaseModel):
    patient: Any = None
    visitType: Any = None
    startDatetime: Any = None
    location: Any = None
    indication: Any = None
    encounters: Any = None