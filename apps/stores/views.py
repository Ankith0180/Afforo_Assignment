from rest_framework.generics import ListAPIView
from .models import Inventory
from .serializers import InventoryListSerializer


class StoreInventoryListView(ListAPIView):
    serializer_class = InventoryListSerializer

    def get_queryset(self):
        store_id = self.kwargs["store_id"]
        return (
            Inventory.objects.filter(store_id=store_id)
            .select_related("product__category")
            .order_by("product__title")
        )
