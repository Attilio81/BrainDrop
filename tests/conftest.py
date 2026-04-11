# tests/conftest.py
import pytest
from bot.config import get_settings

@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
