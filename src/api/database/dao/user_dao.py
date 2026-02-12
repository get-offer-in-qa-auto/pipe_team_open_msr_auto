from __future__ import annotations

import datetime
from dataclasses import dataclass


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
    secret_question: str | None
    secret_answer: str | None
    creator: int
    date_created: datetime.datetime
    changed_by: int | None
    date_changed: datetime.datetime | None
    person_id: int
    retired: bool | None
    retired_by: int | None
    date_retired: datetime.datetime | None
    retire_reason: str | None
    uuid: str
    activation_key: str | None
    email: str | None