import allure
from typing import Protocol, Optional, Union

from src.api.models.base_model import BaseModel


class CrudEndPointInterface(Protocol):
    @allure.step("post")
    def post(self, model: BaseModel) -> BaseModel: ...

    @allure.step("get")
    def get(self, model: Optional[BaseModel] = None, id : Optional[int] = None) -> BaseModel: ...

    @allure.step("update")
    def update(self, model: Optional[BaseModel] = None, id: Optional[int] = None) -> BaseModel: ...

    @allure.step("delete")
    def delete(self, id: int) -> Union[BaseModel, bool]: ...
