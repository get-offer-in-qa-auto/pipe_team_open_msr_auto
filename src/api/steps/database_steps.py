from typing import List, Optional

from src.api.database.dao.patient_dao import PatientDao
from src.api.database.dao.patient_identifier_dao import PatientIdentifierDao
from src.api.database.dao.person_dao import PersonDao, PersonAddressDao
from src.api.database.dao.person_name_dao import PersonNameDao
from src.api.database.dao.user_dao import UserDao
from src.api.database.db_client import DBRequest, RequestType, Condition
from src.api.models.comparison.dao_and_model_assertions import DaoAndModelAssertions
from src.api.models.requests.create_patient_from_person_request import PatientIdentifierRequest
from datetime import datetime, timezone

from src.api.database.dao.visit_dao import VisitDao
from src.api.database.db_client import fetch_one
from src.api.models.requests.create_visit_request import CreateVisitRequest


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
    def get_user_by_uuid(user_uuid: str) -> UserDao:
        return (
            DBRequest.builder()
            .request_type(RequestType.SELECT)
            .table("users")
            .where(Condition.equal_to("uuid", user_uuid))
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
    def find_person_name_by_given_and_last_name(given_name: str, family_name: str):
        return (
            DBRequest.builder()
            .request_type(RequestType.SELECT)
            .table("person_name")
            .where(Condition.equal_to("given_name", given_name).and_(Condition.equal_to("family_name", family_name)))
            .extract_optional_as(PersonNameDao)
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
    def get_all_patients() -> List[PatientDao]:
        return (
            DBRequest.builder()
            .request_type(RequestType.SELECT)
            .table("patient")
            .extract_all_as(PatientDao)
        )

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

    # Visit
    @staticmethod
    def get_visit_by_uuid(visit_uuid: str) -> VisitDao:
        return (
            DBRequest.builder()
            .request_type(RequestType.SELECT)
            .table("visit")
            .where(Condition.equal_to("uuid", visit_uuid))
            .extract_as(VisitDao)
        )

    @staticmethod
    def _id_by_uuid(table: str, id_col: str, uuid: str) -> int:
        row = fetch_one(
            f"SELECT {id_col} AS id FROM {table} WHERE uuid = %s LIMIT 1",
            (uuid,)
        )
        assert row is not None, f"Row not found in `{table}` by uuid={uuid}"
        return int(row["id"])

    @staticmethod
    def _parse_iso_utc(dt_str: str) -> datetime:
        # "2026-02-14T12:34:56.789Z" -> naive datetime (UTC)
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt

    @staticmethod
    def verify_visit_persisted(visit_uuid: str, req: CreateVisitRequest) -> None:
        visit = DatabaseSteps.get_visit_by_uuid(visit_uuid)
        assert not visit.voided, f"Visit {visit_uuid} is voided in DB (raw={visit.voided})"

        person_dao = DatabaseSteps.get_person_by_uuid(req.patient)
        assert visit.patient_id == person_dao.person_id, (
            f"DB patient_id mismatch. expected={person_dao.person_id}, actual={visit.patient_id}"
        )

        expected_visit_type_id = DatabaseSteps._id_by_uuid("visit_type", "visit_type_id", req.visitType)
        assert visit.visit_type_id == expected_visit_type_id, (
            f"DB visit_type_id mismatch. expected={expected_visit_type_id}, actual={visit.visit_type_id}"
        )

        expected_location_id = DatabaseSteps._id_by_uuid("location", "location_id", req.location)
        assert visit.location_id == expected_location_id, (
            f"DB location_id mismatch. expected={expected_location_id}, actual={visit.location_id}"
        )

        expected_start = DatabaseSteps._parse_iso_utc(req.startDatetime).replace(microsecond=0)
        actual_start = visit.date_started.replace(microsecond=0)
        assert actual_start == expected_start, (
            f"DB date_started mismatch. expected={expected_start}, actual={actual_start}"
        )

        if req.stopDatetime is None:
            assert visit.date_stopped is None, f"Expected date_stopped NULL, got {visit.date_stopped}"
        else:
            expected_stop = DatabaseSteps._parse_iso_utc(req.stopDatetime).replace(microsecond=0)
            actual_stop = visit.date_stopped.replace(microsecond=0) if visit.date_stopped else None
            assert actual_stop == expected_stop, (
                f"DB date_stopped mismatch. expected={expected_stop}, actual={actual_stop}"
            )

    @staticmethod
    def count_visits_by_patient_id(patient_id: int) -> int:
        row = fetch_one(
            "SELECT COUNT(*) AS cnt FROM visit WHERE patient_id = %s",
            (patient_id,)
        )
        assert row is not None and "cnt" in row, f"Failed to count visits for patient_id={patient_id}"
        return int(row["cnt"])

    @staticmethod
    def get_visit_row_by_uuid(visit_uuid: str):
        return fetch_one(
            "SELECT visit_id, uuid, voided, voided_by, date_voided, void_reason FROM visit WHERE uuid = %s LIMIT 1",
            (visit_uuid,)
        )

    @staticmethod
    def verify_visit_deleted_in_db(visit_uuid: str) -> None:
        row = DatabaseSteps.get_visit_row_by_uuid(visit_uuid)

        if row is None:
            return

        assert bool(row["voided"]) is False, (
            f"Visit exists in DB but not voided. uuid={visit_uuid}, voided={row['voided']}, "
            f"voided_by={row.get('voided_by')}, date_voided={row.get('date_voided')}, "
            f"reason={row.get('void_reason')}"
        )

    @staticmethod
    def verify_visit_stop_datetime_updated_in_db(visit_uuid: str, stop_datetime_iso: str) -> None:
        row = fetch_one(
            "SELECT uuid, voided, date_stopped FROM visit WHERE uuid = %s LIMIT 1",
            (visit_uuid,)
        )
        assert row is not None, f"Visit not found in DB by uuid={visit_uuid}"

        assert not bool(row["voided"]), f"Visit is voided in DB, uuid={visit_uuid}, voided={row['voided']}"

        assert row["date_stopped"] is not None, f"date_stopped is NULL in DB after update, uuid={visit_uuid}"

        expected_stop = DatabaseSteps._parse_iso_utc(stop_datetime_iso).replace(microsecond=0)
        actual_stop = row["date_stopped"].replace(microsecond=0)

        assert actual_stop == expected_stop, (
            f"DB date_stopped mismatch for uuid={visit_uuid}.\n"
            f"Expected (sec): {expected_stop}\n"
            f"Got (sec):      {actual_stop}\n"
            f"Raw got:        {row['date_stopped']}"
        )

    @staticmethod
    def delete_log_entry_for_user(user_id: int):
        deleted_logs = (
            DBRequest.builder()
            .request_type(RequestType.DELETE)
            .table("idgen_log_entry")
            .where(Condition.equal_to("generated_by", user_id))
            .execute()
        )
        return deleted_logs
