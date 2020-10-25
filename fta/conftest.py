import pytest

from fta.users.models import User
from fta.users.tests.factories import UserFactory


@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir):
    settings.MEDIA_ROOT = tmpdir.strpath #afds


@pytest.fixture
def user() -> User:
    return UserFactory()
