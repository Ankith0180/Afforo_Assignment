import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.products.models import Product, Category


@pytest.mark.django_db
def test_product_search_basic():
    client = APIClient()
    cat = Category.objects.create(name="Electronics")
    Product.objects.create(title="iPhone 15", price=1000, category=cat)
    Product.objects.create(title="Samsung TV", price=1500, category=cat)

    url = reverse("product-search")
    resp = client.get(url, {"q": "iphone"})
    assert resp.status_code == 200
    assert resp.data["count"] == 1
    assert resp.data["results"][0]["title"].startswith("iPhone")
