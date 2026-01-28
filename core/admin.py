from django.contrib import admin
from .models import PickupRequest, WasteGuideItem


@admin.register(PickupRequest)
class PickupRequestAdmin(admin.ModelAdmin):
    list_display = ("full_name", "waste_type", "quantity", "status", "slot", "created_at")
    list_filter = ("waste_type", "status", "slot")
    search_fields = ("full_name", "phone", "address")


@admin.register(WasteGuideItem)
class WasteGuideItemAdmin(admin.ModelAdmin):
    list_display = ("item_name", "category", "instructions")
    list_filter = ("category",)
    search_fields = ("item_name",)
