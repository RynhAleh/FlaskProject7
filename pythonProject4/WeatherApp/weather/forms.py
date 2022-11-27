from django import forms
from .models import City


class CityForm(forms.ModelForm):
    class Meta:
        model = City
        fields = ["name"]
        widgets = {"name":  forms.TextInput(attrs={'class': 'form-input form-control'})}


class DelForm(forms.ModelForm):
    class Meta:
        model = City
        fields = ["id"]
