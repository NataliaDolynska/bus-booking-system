# forms.py
from apps.gtfs.models import GTFSData
from django import forms


class GTFSUploadForm(forms.ModelForm):
    class Meta:
        model = GTFSData
        fields = ['name', 'file']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Dataset Name'}),
        }

