from src.api.steps.admin_steps import AdminSteps


class ApiManager:
    def __init__(self, create_object: list):
        self.admin_steps = AdminSteps(create_object)
