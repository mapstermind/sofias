import pytest
from django.core.exceptions import ImproperlyConfigured

from config.settings import required_env


def test_required_env_returns_the_value(monkeypatch):
    monkeypatch.setenv("SOFIAS_TEST_SECRET", "value")

    assert required_env("SOFIAS_TEST_SECRET") == "value"


@pytest.mark.parametrize("value", [None, ""])
def test_required_env_refuses_a_missing_or_empty_value(monkeypatch, value):
    if value is None:
        monkeypatch.delenv("SOFIAS_TEST_SECRET", raising=False)
    else:
        monkeypatch.setenv("SOFIAS_TEST_SECRET", value)

    with pytest.raises(ImproperlyConfigured, match="SOFIAS_TEST_SECRET"):
        required_env("SOFIAS_TEST_SECRET")
