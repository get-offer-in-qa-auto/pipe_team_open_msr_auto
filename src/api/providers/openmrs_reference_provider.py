import random


class OpenMRSReferenceProvider:

    def __init__(self):
        self.api = None
        self._identifier_types = None
        self._locations = None

    def bind(self, api_manager):
        self.api = api_manager.user_steps

    # ---------- IDENTIFIER TYPES ----------

    def _load_identifier_types(self):
        if self._identifier_types is None:
            resp = self.api.get_patient_identifier_types()

            self._identifier_types = [
                i.uuid
                for i in resp.results
                if "Luhn" in getattr(i, "display", "")
                   or "OpenMRS ID" in getattr(i, "display", "")
            ]

            if not self._identifier_types:
                raise RuntimeError(
                    "OpenMRS misconfigured: no LuhnMod30 identifier type found"
                )

    def get_required_identifier_type_uuid(self) -> str:
        self._load_identifier_types()
        return random.choice(self._identifier_types)

    def get_random_identifier_type_uuid(self) -> str:
        return self.get_required_identifier_type_uuid()

    # ---------- LOCATIONS ----------

    def _load_locations(self):
        if self._locations is None:
            resp = self.api.get_locations()
            self._locations = [l.uuid for l in resp.results]

    def get_random_location_uuid(self) -> str:
        self._load_locations()
        return random.choice(self._locations)
