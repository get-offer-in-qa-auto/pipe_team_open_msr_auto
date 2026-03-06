import allure
from typing import List

from src.api.models.requests.base_create_user_request import BaseCreateUserRequest


class SessionStorage:
    _users: List[BaseCreateUserRequest] = []

    @classmethod
    @allure.step("add_users")
    def add_users(cls, users: List[BaseCreateUserRequest]) -> None:
        for user in list(users):
            cls._users.append(user)

    @classmethod
    @allure.step("get_user")
    def get_user(cls, index: int = 0) -> BaseCreateUserRequest:
        if index >= len(cls._users):
            raise IndexError(
                f"User index (0-based) out of range: {index}; total={len(cls._users)}"
            )
        return cls._users[index]

    @classmethod
    @allure.step("clear")
    def clear(cls):
        cls._users.clear()