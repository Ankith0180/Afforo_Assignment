from django.db import models
from django.db.models import Q, Case, When, IntegerField, OuterRef, Subquery
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework import serializers, status
from rest_framework.views import APIView
from rest_framework.response import Response

from apps.products.models import Product
from apps.stores.models import Inventory
from .throttling import SuggestRateThrottle


class ProductSearchSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name")
    quantity = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = ["id", "title", "description", "price", "category_name", "quantity"]


class ProductSearchPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class ProductSearchView(ListAPIView):
    serializer_class = ProductSearchSerializer
    pagination_class = ProductSearchPagination

    def get_queryset(self):
        qs = Product.objects.select_related("category")
        request = self.request
        q = request.query_params.get("q")
        category_id = request.query_params.get("category")
        price_min = request.query_params.get("price_min")
        price_max = request.query_params.get("price_max")
        store_id = request.query_params.get("store_id")
        in_stock = request.query_params.get("in_stock")
        sort = request.query_params.get("sort")  # price|newest|relevance

        if q:
            qs = qs.filter(
                Q(title__icontains=q)
                | Q(description__icontains=q)
                | Q(category__name__icontains=q)
            )

        if category_id:
            qs = qs.filter(category_id=category_id)

        if price_min:
            qs = qs.filter(price__gte=price_min)
        if price_max:
            qs = qs.filter(price__lte=price_max)

        # annotate qty for a given store if provided
        if store_id:
            inv_sub = Inventory.objects.filter(
                store_id=store_id, product_id=OuterRef("pk")
            ).values("quantity")[:1]
            qs = qs.annotate(quantity=Subquery(inv_sub))
            if in_stock == "true":
                qs = qs.filter(quantity__gt=0)
        else:
            qs = qs.annotate(quantity=models.Value(None, IntegerField()))

        # simple relevance scoring
        if q:
            qs = qs.annotate(
                relevance=Case(
                    When(title__icontains=q, then=3),
                    When(description__icontains=q, then=2),
                    When(category__name__icontains=q, then=1),
                    default=0,
                    output_field=IntegerField(),
                )
            )
        else:
            qs = qs.annotate(relevance=models.Value(0, IntegerField()))

        if sort == "price":
            qs = qs.order_by("price")
        elif sort == "newest":
            qs = qs.order_by("-created_at")
        elif sort == "relevance" and q:
            qs = qs.order_by("-relevance", "title")
        else:
            qs = qs.order_by("title")

        return qs

    def list(self, request, *args, **kwargs):
        # Get the standard paginated response from DRF
        response = super().list(request, *args, **kwargs)

        # DRF default: {"count": X, "next": ..., "previous": ..., "results": [...]}
        paginated = response.data

        # Wrap into the shape we want, but KEEP results as a list
        response.data = {
            "count": paginated.get("count", 0),
            "page": self.paginator.page.number,
            "page_size": self.paginator.page.paginator.per_page,
            "results": paginated.get("results", []),
        }
        return response


class ProductSuggestView(APIView):
    throttle_classes = [SuggestRateThrottle]

    def get(self, request):
        q = request.query_params.get("q", "").strip()
        if len(q) < 3:
            return Response(
                {"detail": "Minimum 3 characters required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qs = (
            Product.objects.filter(title__icontains=q)
            .annotate(
                is_prefix=Case(
                    When(title__istartswith=q, then=0),
                    default=1,
                    output_field=IntegerField(),
                )
            )
            .order_by("is_prefix", "title")[:10]
        )
        titles = list(qs.values_list("title", flat=True))
        return Response({"suggestions": titles})
