from typing import List, Optional

from src.api.models.base_model import BaseModel


class VisitTypeLink(BaseModel):
    rel: str
    uri: str
    resourceAlias: Optional[str] = None


class VisitTypeResult(BaseModel):
    uuid: str
    display: str
    links: Optional[List[VisitTypeLink]] = None


class VisitTypeListResponse(BaseModel):
    results: List[VisitTypeResult]
    links: Optional[List[VisitTypeLink]] = None