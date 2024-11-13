# forms.py

from .models import GTFSData
from django import forms
from .models import BookingRestriction

class GTFSUploadForm(forms.ModelForm):
    class Meta:
        model = GTFSData
        fields = ['name', 'file']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Dataset Name'}),
        }


class BookingRestrictionForm(forms.ModelForm):
    class Meta:
        model = BookingRestriction
        fields = '__all__'
