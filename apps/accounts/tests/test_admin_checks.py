import pytest
from django.core.management import call_command


@pytest.mark.django_db
def test_django_system_checks_pass():
    """The admin composes field lists by hand, so a renamed field breaks silently
    until `check` runs. `admin.E108`/`E012` are the failures this catches."""
    call_command("check")
