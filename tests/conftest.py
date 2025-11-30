# tests/conftest.py
import os
import django
import pytest

# Make sure Django knows which settings to use
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

# Initialize Django (so REST_FRAMEWORK & INSTALLED_APPS are loaded)
django.setup()


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    # gives all tests DB access by default
    pass
