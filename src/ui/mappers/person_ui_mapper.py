import allure
from dataclasses import dataclass
from datetime import date
from src.api.models.requests.create_person_request import CreatePersonRequest


@dataclass
class UiPatientData:
    given: str
    family: str
    gender: str
    age: int


class PersonUiMapper:

    GENDER_MAP = {
        "M": "male",
        "F": "female",
        "U": "unknown",
    }

    @staticmethod
    @allure.step("from_request")
    def from_request(req: CreatePersonRequest) -> UiPatientData:
        name = req.names[0]

        birthdate = date.fromisoformat(req.birthdate)
        today = date.today()

        age = today.year - birthdate.year - (
            (today.month, today.day) < (birthdate.month, birthdate.day)
        )

        return UiPatientData(
            given=name.givenName,
            family=name.familyName,
            gender=PersonUiMapper.GENDER_MAP[req.gender],
            age=age,
        )
