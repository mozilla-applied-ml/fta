from crispy_forms import layout
from crispy_forms.helper import FormHelper
from django import forms

from .models import SAMPLE_SOFTWARE_PARSERS, Sample


# Create the form class.
class UploadSampleForm(forms.ModelForm):
    class Meta:
        model = Sample
        fields = ["frozen_page", "freeze_software", "notes"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(layout.Submit("submit", "Submit"))

    freeze_software = forms.CharField(
        widget=forms.Select(choices=SAMPLE_SOFTWARE_PARSERS),
    )
    frozen_page = forms.FileField()
    notes = forms.CharField(required=False)


class SampleLabelForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(
            layout.Submit(
                name="submit",
                value="Submit",
                css_id="submit-labels",
            )
        )
        self.helper.add_input(
            layout.Hidden(
                name="updated-sample",
                value="updated-sample",
            )
        )
        self.helper.add_input(
            layout.Hidden(
                name="label-data",
                value="label-data",
            )
        )
