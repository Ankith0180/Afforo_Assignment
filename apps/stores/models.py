from django.db import models
from apps.products.models import Product


class Store(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name


class Inventory(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="inventory")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="inventories")
    quantity = models.PositiveIntegerField()

    class Meta:
        unique_together = ("store", "product")

    def __str__(self):
        return f"{self.store} - {self.product} ({self.quantity})"
