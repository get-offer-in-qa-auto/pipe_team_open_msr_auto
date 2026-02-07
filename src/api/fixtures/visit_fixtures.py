import pytest

from src.api.classes.api_manager import ApiManager


@pytest.fixture
def api_manager(created_objects) -> ApiManager:
    return ApiManager(created_objects)