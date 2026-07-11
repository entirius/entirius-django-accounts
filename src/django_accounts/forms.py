# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from django import forms

from .models import AddressFile


class AddressFileForm(forms.ModelForm):
    class Meta:
        model = AddressFile
        fields = ("label", "upload")
