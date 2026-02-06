from src.api.steps.user_steps import UserSteps


class ApiManager:
    def __init__(self, create_object: list):
        self.user_steps = UserSteps(create_object)
