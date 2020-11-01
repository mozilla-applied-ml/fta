import json
from datetime import datetime

from bs4 import BeautifulSoup
from dateutil.parser import parse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import redirect, render, reverse
from django.utils.encoding import smart_str
from django.views.generic import ListView
from django.views.generic.edit import FormView

from .forms import SampleLabelForm, UploadSampleForm
from .models import Label, LabeledElement, LabeledSample, Sample


def get_frozen_metadata(page, freeze_software):
    # Defaults
    url = ""
    freeze_time = datetime.now()
    if freeze_software == "SinglePage":
        soup = BeautifulSoup(page)
        singlefile_comment = soup.html.contents[0]
        pieces = singlefile_comment.strip().split("\n")
        assert pieces[0].startswith("Page saved with SingleFile")
        assert len(pieces) == 3
        url = pieces[1].split("url:")[1].strip()
        raw_time = pieces[2].split("date:")[1].strip().split("(")[0]
        freeze_time = parse(raw_time)
    return url, freeze_time


class UploadSampleView(LoginRequiredMixin, FormView):
    template_name = "samples/upload_sample.html"
    form_class = UploadSampleForm

    def post(self, request, *args, **kwargs):
        # We're just going to manually validate this.
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            frozen_page = smart_str(data["frozen_page"].read())
            freeze_software = data["freeze_software"]
            url, freeze_time = get_frozen_metadata(frozen_page, freeze_software)
            Sample.objects.create(
                frozen_page=frozen_page,
                url=url,
                freeze_time=freeze_time,
                freeze_software=freeze_software,
                notes=data["notes"],
            )
            return redirect("list_samples")
        else:
            return render(request, self.template_name, {"form": form})


class SampleListView(LoginRequiredMixin, ListView):
    model = Sample
    template_name = "samples/list_samples.html"


class SampleLabelView(LoginRequiredMixin, FormView):
    template_name = "samples/label_sample.html"
    form_class = SampleLabelForm

    def get_success_url(self):
        return reverse("label", kwargs=dict(sample=f"{self.sample.original_sample.id}"))

    def dispatch(self, request, *args, **kwargs):
        requested_sample_id = kwargs["sample"]
        try:
            sample = Sample.objects.get(pk=requested_sample_id)
            self.sample, created = LabeledSample.objects.get_or_create(
                original_sample=sample
            )
            if created:
                self.sample.modified_sample = sample.frozen_page
                self.sample.save()
            return super().dispatch(request, *args, **kwargs)
        except Sample.DoesNotExist:
            raise Http404(f"Sample does not exist with ID {requested_sample_id}")

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context["sample"] = self.sample
        context["labels"] = LabeledElement.objects.filter(labeled_sample=self.sample)
        return context

    def post(self, request, *args, **kwargs):
        # We're willy nilly saving user input into database
        # This is only okay while all this is behind a managed login.
        self.sample.modified_sample = request.POST.get("updated-sample", "")
        self.sample.save()
        label_data_list = json.loads(request.POST.get("label-data", ""))
        for label_data in label_data_list:
            label, _ = Label.objects.get_or_create(slug=label_data["label"])
            element, _ = LabeledElement.objects.get_or_create(
                labeled_sample=self.sample,
                data_fta_id=label_data["fta_id"],
            )
            element.label = label
            element.save()
        return super().post(request, *args, **kwargs)
