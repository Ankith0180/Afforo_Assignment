from django.db import transaction
from kombu.exceptions import OperationalError as KombuOperationalError
from redis.exceptions import ConnectionError as RedisConnectionError

from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import ListAPIView

from .models import Order, OrderItem
from apps.stores.models import Store, Inventory
from apps.products.models import Product
from .serializers import OrderCreateSerializer, OrderSerializer
from .tasks import send_order_confirmation_email


class OrderCreateView(APIView):
    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        store_id = serializer.validated_data["store_id"]
        items_data = serializer.validated_data["items"]

        store = get_object_or_404(Store, id=store_id)

        with transaction.atomic():
            order = Order.objects.create(store=store, status=Order.STATUS_PENDING)

            insufficient_stock = False
            inventory_map = {}

            for item in items_data:
                product = get_object_or_404(Product, id=item["product_id"])
                inv = (
                    Inventory.objects.select_for_update()
                    .filter(store=store, product=product)
                    .first()
                )

                qty = item["quantity_requested"]
                if not inv or inv.quantity < qty:
                    insufficient_stock = True

                inventory_map[product.id] = (inv, qty)

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity_requested=qty,
                )

            if insufficient_stock:
                order.status = Order.STATUS_REJECTED
                order.save()
            else:
                # deduct stock
                for inv, qty in inventory_map.values():
                    inv.quantity -= qty
                    inv.save()
                order.status = Order.STATUS_CONFIRMED
                order.save()
                try:
                    send_order_confirmation_email.delay(order.id)
                except (KombuOperationalError, RedisConnectionError):
                    # In local/dev/tests, Celery broker may not be running.
                    # We silently ignore failures here; core order flow still succeeds.
                    pass

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class StoreOrderListView(ListAPIView):
    serializer_class = OrderSerializer

    def get_queryset(self):
        store_id = self.kwargs["store_id"]
        return (
            Order.objects.filter(store_id=store_id)
            .annotate(total_items=Count("items"))
            .select_related("store")
            .prefetch_related("items__product")
            .order_by("-created_at")
        )

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        response = super().list(request, *args, **kwargs)
        for obj, data in zip(queryset, response.data):
            data["total_items"] = obj.total_items
        return response
