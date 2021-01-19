import json
from datetime import datetime

from bs4 import BeautifulSoup
from dateutil.parser import parse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import redirect, render, reverse
from django.utils.encoding import smart_str
from django.views.generic.edit import FormView
from django_tables2 import SingleTableView

from .forms import SampleLabelForm, UploadSampleForm
from .models import Label, LabeledElement, LabeledSample, Sample
from .tables import SampleTable


class SampleListView(LoginRequiredMixin, SingleTableView):
    model = Sample
    template_name = "samples/list_samples.html"
    table_class = SampleTable

    def get_queryset(self, *args, **kwargs):
        requested_label = self.request.GET.get("label", None)
        all_samples = Sample.objects.get_queryset()

        if requested_label == "-":
            filtered_qs = all_samples.filter(nlabels__exact=0)
        else:
            try:
                requested_label = Label.objects.get(slug=requested_label)
                filtered_qs = all_samples.filter(
                    labeled_sample__labeled_elements__label=requested_label
                ).distinct()
            except Label.DoesNotExist:
                # Default to all
                filtered_qs = all_samples
        return filtered_qs


class SampleLabelView(LoginRequiredMixin, FormView):
    template_name = "samples/label_sample.html"
    form_class = SampleLabelForm

    def get_success_url(self):
        # Returns to same page on submit
        # return reverse("label", kwargs=dict(sample=f"{self.sample.original_sample.id}"))

        # Returns to list view
        return reverse("list_samples")

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
        labeled_elements = LabeledElement.objects.filter(labeled_sample=self.sample)
        labels = ", ".join(
            labeled_elements.distinct("label").values_list("label__slug", flat=True)
        )
        context["sample"] = self.sample
        context["labeled_elements"] = labeled_elements
        context["labels"] = labels
        return context

    def post(self, request, *args, **kwargs):
        # We're willy nilly saving user input into database
        # This is only okay while all this is behind a managed login.
        self.sample.modified_sample = request.POST.get("updated-sample", "")
        self.sample.save()
        label_data_list = json.loads(request.POST.get("label-data", "[]"))
        for label_data in label_data_list:
            label, _ = Label.objects.get_or_create(slug=label_data["label"])
            # Make sure that the label overrides the old one.
            try:
                element = LabeledElement.objects.get(
                    labeled_sample=self.sample,
                    data_fta_id=label_data["fta_id"],
                )
            except LabeledElement.DoesNotExist:
                element = LabeledElement(
                    labeled_sample=self.sample,
                    data_fta_id=label_data["fta_id"],
                )
            element.label = label
            element.save()
        return super().post(request, *args, **kwargs)


def get_frozen_metadata(page, freeze_software):
    # Defaults
    url = ""
    freeze_time = datetime.now()
    page_width = None
    page_height = None
    try:
        if freeze_software == "SingleFile":
            soup = BeautifulSoup(page, features="html.parser")
            singlefile_comment = soup.html.contents[0]
            pieces = singlefile_comment.strip().split("\n")
            assert pieces[0].startswith("Page saved with SingleFile")
            assert len(pieces) == 3 or len(pieces) == 5
            url = pieces[1].split("url:")[1].strip()
            raw_time = pieces[2].split("date:")[1].strip().split("(")[0]
            freeze_time = parse(raw_time)
            if len(pieces) == 5:
                page_width = int(pieces[3].split("window width:")[1])
                page_height = int(pieces[4].split("window height:")[1])
        elif freeze_software == "freezedry":
            soup = BeautifulSoup(page, features="html.parser")
            freezedry_link = soup.find("link", rel="original")
            freezedry_datetime = soup.find(
                "meta",
                attrs={
                    "http-equiv": "Memento-Datetime",
                },
            )
            if freezedry_link:
                url = freezedry_link["href"]
            if freezedry_datetime:
                freeze_time = parse(freezedry_datetime["content"])
    except:  # noqa
        # It's okay if it fails. It just means freeze_software declaration
        # was probably wrong, so set to unknown.
        freeze_software = "Unknown"
    return url, freeze_time, freeze_software, page_width, page_height


def sample_from_required(frozen_page, freeze_software, notes):
    url, freeze_time, freeze_software, page_width, page_height = get_frozen_metadata(
        frozen_page, freeze_software
    )
    return Sample(
        frozen_page=frozen_page,
        url=url,
        freeze_time=freeze_time,
        freeze_software=freeze_software,
        notes=notes,
        page_width=page_width,
        page_height=page_height,
    )


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
            sample = sample_from_required(frozen_page, freeze_software, data["notes"])
            sample.save()
            return redirect("list_samples")
        else:
            return render(request, self.template_name, {"form": form})
