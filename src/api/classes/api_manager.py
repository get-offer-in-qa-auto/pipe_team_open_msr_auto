from src.api.steps.database_steps import DatabaseSteps
from src.api.steps.user_steps import UserSteps
from src.api.steps.visit_steps import VisitSteps
from src.api.generators.generator_context import GeneratorContext
from src.api.providers.openmrs_reference_provider import OpenMRSReferenceProvider

class ApiManager:
    def __init__(self, create_object: list):
        self.user_steps = UserSteps(create_object)
        self.visit_steps = VisitSteps(create_object)
        self.database_steps = DatabaseSteps

        # создаём provider БЕЗ api
        self.reference_provider = OpenMRSReferenceProvider()
        self.reference_provider.bind(self)

        GeneratorContext.reference_provider = self.reference_provider
