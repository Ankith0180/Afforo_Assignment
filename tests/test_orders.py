import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.stores.models import Store, Inventory
from apps.products.models import Product, Category


@pytest.mark.django_db
def test_order_rejected_on_insufficient_stock():
    client = APIClient()
    store = Store.objects.create(name="S1")
    cat = Category.objects.create(name="Cat1")
    product = Product.objects.create(title="P1", price=100, category=cat)

    Inventory.objects.create(store=store, product=product, quantity=1)

    url = reverse("order-create")
    payload = {
        "store_id": store.id,
        "items": [{"product_id": product.id, "quantity_requested": 5}],
    }
    resp = client.post(url, payload, format="json")
    assert resp.status_code == 201
    assert resp.data["status"] == "REJECTED"


@pytest.mark.django_db
def test_order_confirmed_on_sufficient_stock_and_stock_deducted():
    client = APIClient()
    store = Store.objects.create(name="S2")
    cat = Category.objects.create(name="Cat2")
    product = Product.objects.create(title="P2", price=100, category=cat)

    Inventory.objects.create(store=store, product=product, quantity=10)

    url = reverse("order-create")
    payload = {
        "store_id": store.id,
        "items": [{"product_id": product.id, "quantity_requested": 3}],
    }
    resp = client.post(url, payload, format="json")
    assert resp.status_code == 201
    assert resp.data["status"] == "CONFIRMED"

    inv = Inventory.objects.get(store=store, product=product)
    assert inv.quantity == 7
