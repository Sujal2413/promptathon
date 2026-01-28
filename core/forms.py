from django import forms
from .models import PickupRequest


class PickupRequestForm(forms.ModelForm):
    class Meta:
        model = PickupRequest
        fields = ["full_name", "phone", "waste_type", "quantity", "address", "slot", "photo"]

        widgets = {
            "full_name": forms.TextInput(attrs={"class": "input", "placeholder": "Your full name"}),
            "phone": forms.TextInput(attrs={"class": "input", "placeholder": "Optional phone"}),
            "waste_type": forms.Select(attrs={"class": "input"}),
            "quantity": forms.Select(attrs={"class": "input"}),
            "address": forms.TextInput(attrs={"class": "input", "placeholder": "House/Flat, Society, Landmark"}),
            "slot": forms.Select(
                choices=[("Morning", "Morning"), ("Evening", "Evening")],
                attrs={"class": "input"},
            ),
            "photo": forms.ClearableFileInput(attrs={"class": "input"}),
        }
