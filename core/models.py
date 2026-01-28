from django.conf import settings
from django.db import models


class PickupRequest(models.Model):
    WASTE_TYPES = [
        ("WET", "Wet"),
        ("DRY", "Dry"),
        ("EWASTE", "E-waste"),
        ("HAZARD", "Hazard"),
    ]

    QUANTITY = [
        ("S", "Small"),
        ("M", "Medium"),
        ("L", "Large"),
    ]

    STATUS = [
        ("REQUESTED", "Requested"),
        ("ASSIGNED", "Assigned"),
        ("PICKED", "Picked"),
    ]

    # User account who created the request (normal user)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pickup_requests",
    )

    full_name = models.CharField(max_length=80)
    phone = models.CharField(max_length=20, blank=True)
    waste_type = models.CharField(max_length=10, choices=WASTE_TYPES)
    quantity = models.CharField(max_length=1, choices=QUANTITY)
    address = models.CharField(max_length=200)
    slot = models.CharField(max_length=20, default="Morning")
    photo = models.ImageField(upload_to="waste_photos/", blank=True, null=True)
    status = models.CharField(max_length=12, choices=STATUS, default="REQUESTED")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} - {self.get_waste_type_display()} ({self.status})"


class WasteGuideItem(models.Model):
    CATEGORY = [
        ("WET", "Wet"),
        ("DRY", "Dry"),
        ("EWASTE", "E-waste"),
        ("HAZARD", "Hazard"),
    ]

    item_name = models.CharField(max_length=80, unique=True)
    category = models.CharField(max_length=10, choices=CATEGORY)
    instructions = models.CharField(max_length=220)

    def __str__(self):
        return self.item_name
