from crispy_forms.helper import FormHelper
from crispy_forms.layout import Button, Submit
from django import forms

from .models import SAMPLE_SOFTWARE_PARSERS, Label, Sample


# Create the form class.
class UploadSampleForm(forms.ModelForm):
    class Meta:
        model = Sample
        fields = ["frozen_page", "freeze_software", "notes"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit("submit", "Submit"))

    freeze_software = forms.CharField(
        widget=forms.Select(choices=SAMPLE_SOFTWARE_PARSERS),
    )
    frozen_page = forms.FileField()
    notes = forms.CharField(required=False)


class SampleLabelForm(forms.ModelForm):
    class Meta:
        model = Label
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit("submit", "Submit"))
        self.helper.add_input(
            Button(
                name="btn-pick",
                value="Toggle element picking",
                css_id="btn-pick",
                css_class="btn-light",
            )
        )
