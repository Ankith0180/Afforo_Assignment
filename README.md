# Aforro Backend Assignment

This is a Django + Django REST Framework backend for a simplified marketplace / inventory system.

It implements:

- **Order placement** with atomic inventory checks and updates  
- **Store-wise inventory listing**  
- **Product search** with filters, sorting, and store-aware stock info  
- **Autocomplete suggestions** with Redis-backed rate limiting (graceful fallback if Redis is down)  
- **Async order confirmation email** via Celery (non-blocking, fails gracefully if broker is down)  
- **Data seeding** and **pytest test suite**

---

## Tech Stack

- Python 3.11+
- Django 5.x
- Django REST Framework
- PostgreSQL (via Docker) or SQLite for local dev
- Redis (for rate limiting + Celery broker/result backend)
- Celery
- pytest + pytest-django

---

## Project Structure

```text
aforro_backend/
├─ manage.py
├─ project/
│  ├─ __init__.py
│  ├─ settings.py
│  ├─ urls.py
│  ├─ celery.py
│  ├─ wsgi.py
├─ apps/
│  ├─ products/
│  │  ├─ models.py        # Category, Product
│  │  ├─ serializers.py
│  │  ├─ views.py         # optional product list
│  │  ├─ urls.py
│  │  ├─ admin.py
│  ├─ stores/
│  │  ├─ models.py        # Store, Inventory
│  │  ├─ serializers.py
│  │  ├─ views.py         # store inventory listing
│  │  ├─ urls.py
│  │  ├─ admin.py
│  ├─ orders/
│  │  ├─ models.py        # Order, OrderItem
│  │  ├─ serializers.py
│  │  ├─ views.py         # order create + store order list
│  │  ├─ urls.py
│  │  ├─ tasks.py         # Celery email task
│  │  ├─ admin.py
│  │  ├─ management/
│  │  │  └─ commands/
│  │  │     └─ seed_data.py  # seed script (hooked into installed app)
│  ├─ search/
│  │  ├─ views.py         # product search + suggest
│  │  ├─ urls.py
│  │  ├─ throttling.py    # Redis-based rate limiting (graceful fallback)
├─ tests/
│  ├─ conftest.py
│  ├─ test_orders.py
│  ├─ test_search.py
│  ├─ test_rate_limit.py
├─ requirements.txt
├─ docker-compose.yml
├─ Dockerfile
├─ pytest.ini
└─ README.md





1️⃣ Test: Create an Order
POST /orders/
Postman Setup

Method: POST

URL: http://127.0.0.1:8000/orders/

Headers:

Content-Type: application/json


Body → Raw → JSON

{
  "store_id": 1,
  "items": [
    { "product_id": 10, "quantity_requested": 3 },
    { "product_id": 11, "quantity_requested": 2 }
  ]
}

Expected Success Response (201)
{
  "id": 123,
  "store": 1,
  "status": "CONFIRMED",
  "created_at": "2025-11-29T16:00:00Z",
  "items": [
    { "id": 1, "product": 10, "product_title": "iPhone 15", "quantity_requested": 3 },
    { "id": 2, "product": 11, "product_title": "Samsung TV", "quantity_requested": 2 }
  ]
}

If stock is insufficient → REJECTED (200)
{
  "id": 124,
  "store": 1,
  "status": "REJECTED",
  "created_at": "2025-11-29T16:00:10Z",
  "items": [
    { "id": 3, "product": 11, "product_title": "Samsung TV", "quantity_requested": 5 }
  ],
  "reason": "Insufficient stock for one or more items."
}

2️⃣ Test: Get Orders for a Store
GET /orders/store/<store_id>/
Sample URL
http://127.0.0.1:8000/orders/store/1/

Expected Response
[
  {
    "id": 123,
    "store": 1,
    "status": "CONFIRMED",
    "total_items": 2,
    "created_at": "2025-11-29T16:00:00Z",
    "items": [
      { "product_title": "iPhone 15", "quantity_requested": 3 },
      { "product_title": "Samsung TV", "quantity_requested": 2 }
    ]
  }
]

3️⃣ Test: Get Store Inventory
GET /stores/<store_id>/inventory/
Sample URL
http://127.0.0.1:8000/stores/1/inventory/

Expected Response
[
  {
    "id": 10,
    "product_title": "iPhone 15",
    "price": "1000.00",
    "category_name": "Electronics",
    "quantity": 7
  },
  {
    "id": 11,
    "product_title": "Samsung TV",
    "price": "1500.00",
    "category_name": "Electronics",
    "quantity": 3
  }
]

4️⃣ Test: Product Search
GET /api/search/products/
Postman Setup

Method: GET

URL:

http://127.0.0.1:8000/api/search/products/?q=iphone&store_id=1&in_stock=true

Expected Response
{
  "count": 1,
  "page": 1,
  "page_size": 20,
  "results": [
    {
      "id": 10,
      "title": "iPhone 15",
      "description": "Latest generation Apple smartphone.",
      "price": "1000.00",
      "category_name": "Electronics",
      "quantity": 2
    }
  ]
}

5️⃣ Test: Autocomplete Suggestions
GET /api/search/suggest/?q=iph
Postman Setup

Method: GET

URL:

http://127.0.0.1:8000/api/search/suggest/?q=iph

Expected Response
{
  "suggestions": [
    "iPhone 15",
    "iPhone 15 Pro",
    "iPhone Charger Adapter"
  ]
}

⚠️ Note

If Redis is NOT running, you will still get suggestions, because rate limiting gracefully skips.

6️⃣ Seed Test Data (Postman Optional)

To quickly load default products/stores:

Command:
python manage.py seed_data


Populates:

Categories

Products

Multiple stores

Inventory per store

7️⃣ Testing Celery Email Sending (Optional)
Trigger by placing an order:

Celery runs automatically if Redis + Celery worker are running.

You should see a log like:

[Celery] Sending confirmation email for Order #123


If Celery is NOT running:

The order still succeeds

Email silently fails (by design)