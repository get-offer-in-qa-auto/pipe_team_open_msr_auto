from __future__ import annotations

from typing import List, Optional, Any

from src.api.models.base_model import BaseModel


class Link(BaseModel):
    rel: str
    uri: str
    resourceAlias: Optional[str] = None


class Ref(BaseModel):
    uuid: str
    display: Optional[str] = None
    links: Optional[List[Link]] = None


class VisitCreateResponse(BaseModel):
    """Response for POST /visit.
    """

    uuid: str
    display: Optional[str] = None
    patient: Optional[Ref] = None
    visitType: Optional[Ref] = None
    location: Optional[Ref] = None
    startDatetime: Optional[str] = None
    stopDatetime: Optional[str] = None
    indication: Optional[Any] = None
    encounters: Optional[List[Any]] = None
    links: Optional[List[Link]] = None
    resourceVersion: Optional[str] = None