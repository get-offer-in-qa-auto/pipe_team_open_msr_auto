from src.api.models.comparison.model_assertions import ModelAssertions


class PersonCreationVerifier:
    def __init__(self, api_manager):
        self.api_manager = api_manager

    def verify_person_created(self, person_uuid, expected_request=None):
        full = self.api_manager.user_steps.get_person_full(person_uuid)

        assert full.uuid == person_uuid
        assert full.voided is False
        assert full.preferredName
        assert full.preferredName.uuid

        if expected_request:
            ModelAssertions(expected_request, full).match()
        return full