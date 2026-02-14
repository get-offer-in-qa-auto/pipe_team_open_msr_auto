from typing import List, Optional

from src.api.database.dao.patient_dao import PatientDao
from src.api.database.dao.patient_identifier_dao import PatientIdentifierDao
from src.api.database.dao.person_dao import PersonDao, PersonAddressDao
from src.api.database.dao.user_dao import UserDao
from src.api.database.db_client import DBRequest, RequestType, Condition
from src.api.models.comparison.dao_and_model_assertions import DaoAndModelAssertions
from src.api.models.requests.create_patient_from_person_request import PatientIdentifierRequest


class DatabaseSteps:
    @staticmethod
    def get_user_by_username(username: str) -> UserDao:
        return (
            DBRequest.builder()
            .request_type(RequestType.SELECT)
            .table("users")
            .where(Condition.equal_to("username", username))
            .extract_as(UserDao)
        )

    @staticmethod
    def get_patient_by_id(patient_id: int) -> PatientDao:
        return (
            DBRequest.builder()
            .request_type(RequestType.SELECT)
            .table("patient")
            .where(Condition.equal_to("patient_id", patient_id))
            .extract_as(PatientDao)
        )

    @staticmethod
    def find_patient_by_id(patient_id: int) -> Optional[PatientDao]:
        return (
            DBRequest.builder()
            .request_type(RequestType.SELECT)
            .table("patient")
            .where(Condition.equal_to("patient_id", patient_id))
            .extract_optional_as(PatientDao)
        )

    @staticmethod
    def get_patient_identifier_by_identifier(identifier: str) -> PatientIdentifierDao:
        return (
            DBRequest.builder()
            .request_type(RequestType.SELECT)
            .table("patient_identifier")
            .where(Condition.equal_to("identifier", identifier))
            .extract_as(PatientIdentifierDao)
        )

    @staticmethod
    def get_person_by_address(address: str) -> PersonAddressDao:
        return (
            DBRequest.builder()
            .request_type(RequestType.SELECT)
            .table("person_address")
            .where(Condition.equal_to("address1", address))
            .extract_as(PersonAddressDao)
        )

    @staticmethod
    def get_person_by_uuid(uuid: str):
        return (
            DBRequest.builder()
            .request_type(RequestType.SELECT)
            .table("person")
            .where(Condition.equal_to("uuid", uuid))
            .extract_as(PersonDao)
        )

    @staticmethod
    def get_person_by_id(id: int):
        return (
            DBRequest.builder()
            .request_type(RequestType.SELECT)
            .table("person")
            .where(Condition.equal_to("person_id", id))
            .extract_as(PersonDao)
        )

    @staticmethod
    def verify_patient_created_from_existing_person(person_uuid: str, identifiers: List[PatientIdentifierRequest]):
        person_dao = DatabaseSteps.get_person_by_uuid(person_uuid)
        assert person_dao.voided == False

        patient_dao = DatabaseSteps.get_patient_by_id(person_dao.person_id)
        assert patient_dao.voided == False

        for identifier in identifiers:
            patient_identifier_dao = DatabaseSteps.get_patient_identifier_by_identifier(identifier.identifier)
            assert patient_identifier_dao.voided == False
            assert patient_identifier_dao.patient_id == person_dao.person_id
            DaoAndModelAssertions.assert_that(identifier, patient_identifier_dao).match()

    @staticmethod
    def verify_patient_does_not_exist(person_uuid: str):
        person_dao = DatabaseSteps.get_person_by_uuid(person_uuid)
        assert person_dao.voided == False

        patient_dao = DatabaseSteps.find_patient_by_id(person_dao.person_id)
        assert patient_dao is None, f"Patient '{person_dao.person_id}' should NOT exist in DB after invalid create, but was found: {patient_dao}"

    @staticmethod
    def get_person_by_birthdate(person_birthdate) -> Optional[PersonDao]:
        try:
            return (
                DBRequest.builder()
                .request_type(RequestType.SELECT)
                .table("person")
                .where(Condition.equal_to("birthdate", person_birthdate))
                .extract_as(PersonDao)
            )
        except AssertionError:
            return None

    @staticmethod
    def verify_person_does_not_exist(person_birthdate: str):
        person_dao = DatabaseSteps.get_person_by_birthdate(person_birthdate)
        assert person_dao is None, f"Person '{person_dao.person_id}' should NOT exist in DB after invalid create"


