from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Optional


@dataclass
class UserDao:
    """
    Representation of a row in 'customers' table.
    Field names are expected to match DB columns (snake_case).
    """

    user_id: int
    system_id: str
    username: str
    password: str
    salt: str
    secret_question: Optional[str]
    secret_answer: Optional[str]
    creator: int
    date_created: datetime.datetime
    changed_by: Optional[int]
    date_changed: Optional[datetime.datetime]
    person_id: int
    retired: bool | None
    retired_by: Optional[int]
    date_retired: Optional[datetime.datetime]
    retire_reason: Optional[str]
    uuid: str
    activation_key: Optional[str]
    email: Optional[str]