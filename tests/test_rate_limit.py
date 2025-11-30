import pytest
from django.urls import reverse
from rest_framework.test import APIClient
import redis
from redis.exceptions import ConnectionError as RedisConnectionError, TimeoutError
from django.conf import settings


def redis_available():
    try:
        r = redis.Redis.from_url(settings.REDIS_URL)
        r.ping()
        return True
    except (RedisConnectionError, TimeoutError):
        return False


@pytest.mark.skipif(
    not redis_available(),
    reason="Redis is not running; skipping rate limit tests."
)
@pytest.mark.django_db
def test_suggest_min_length():
    client = APIClient()
    url = reverse("product-suggest")
    resp = client.get(url, {"q": "ab"})
    assert resp.status_code == 400
    assert "Minimum 3 characters" in resp.data["detail"]


@pytest.mark.skipif(
    not redis_available(),
    reason="Redis is not running; skipping rate limit tests."
)
@pytest.mark.django_db
def test_suggest_rate_limit():
    """
    This test requires Redis to enforce rate limiting.
    If Redis is not running, test will be skipped.
    """
    client = APIClient()
    url = reverse("product-suggest")

    limited = False
    last_status = None

    # Make 25 calls to trigger 20 req/min throttle
    for _ in range(25):
        resp = client.get(url, {"q": "testquery"})
        last_status = resp.status_code
        if last_status == 429:
            limited = True
            break

    assert limited, f"Expected rate limiting (429), got last status {last_status}"
