from django.contrib import admin
from .models import Store, Inventory


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "location")


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ("id", "store", "product", "quantity")
    list_filter = ("store",)
