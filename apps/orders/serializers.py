from rest_framework import serializers
from .models import Order, OrderItem


class OrderItemCreateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity_requested = serializers.IntegerField(min_value=1)


class OrderCreateSerializer(serializers.Serializer):
    store_id = serializers.IntegerField()
    items = OrderItemCreateSerializer(many=True)

    def validate(self, data):
        if not data["items"]:
            raise serializers.ValidationError("At least one item is required.")
        return data


class OrderItemSerializer(serializers.ModelSerializer):
    product_title = serializers.CharField(source="product.title", read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "product", "product_title", "quantity_requested"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "store", "status", "created_at", "items"]
