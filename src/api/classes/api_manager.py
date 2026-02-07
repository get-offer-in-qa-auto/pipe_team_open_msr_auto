from src.api.steps.admin_steps import AdminSteps
from src.api.steps.visit_steps import VisitSteps


class ApiManager:
    def __init__(self, create_object: list):
        self.admin_steps = AdminSteps(create_object)
        self.visit_steps = VisitSteps(create_object)
