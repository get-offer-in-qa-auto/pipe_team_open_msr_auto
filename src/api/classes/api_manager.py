import allure
from src.api.steps.database_steps import DatabaseSteps
from src.api.steps.user_steps import UserSteps
from src.api.steps.visit_steps import VisitSteps


class ApiManager:
    @allure.step("__init__")
    def __init__(self, create_object: list):
        self.user_steps = UserSteps(create_object)
        self.visit_steps = VisitSteps(create_object)
        self.database_steps = DatabaseSteps
