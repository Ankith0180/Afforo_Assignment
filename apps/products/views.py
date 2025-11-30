from rest_framework.generics import ListAPIView
from .models import Product
from .serializers import ProductSerializer


class ProductListView(ListAPIView):
    queryset = Product.objects.all().select_related("category").order_by("title")
    serializer_class = ProductSerializer
