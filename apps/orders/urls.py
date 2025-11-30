from django.urls import path
from .views import OrderCreateView, StoreOrderListView

urlpatterns = [
    path("", OrderCreateView.as_view(), name="order-create"),
    path("store/<int:store_id>/", StoreOrderListView.as_view(), name="store-orders"),
]
