from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import filesizeformat


class UploadForm(forms.Form):
    upload_file = forms.FileField(
        label='Select an image file'
    )