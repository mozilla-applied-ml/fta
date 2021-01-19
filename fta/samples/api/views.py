from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from ..models import Label, LabeledElement, LabeledSample, Sample
from ..utils import convert_fathom_sample_to_labeled_sample
from ..views import sample_from_required
from .serializers import SampleListSerializer, SampleSerializer


class SampleViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = SampleSerializer
    queryset = Sample.objects.all()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.serializer_action_classes = {
            "list": SampleListSerializer,
            "create": SampleSerializer,
            "retrieve": SampleSerializer,
        }

    def get_serializer_class(self, *args, **kwargs):
        """Instantiate the list of serializers per action from class attribute (must be defined)."""
        kwargs["partial"] = True
        try:
            return self.serializer_action_classes[self.action]
        except (KeyError, AttributeError):
            return super().get_serializer_class()


class AddSampleViewSet(viewsets.ViewSet):
    basename = "add_sample"

    @action(detail=False, methods=["post"])
    def add_sample(self, request, format=None):
        frozen_page = request.data["frozen_page"]
        freeze_software = request.data["freeze_software"]
        notes = request.data["notes"] if "notes" in request.data else ""
        sample = sample_from_required(frozen_page, freeze_software, notes)
        sample.save()
        return Response({"id": sample.id})


class AddLabeledSampleViewSet(viewsets.ViewSet):
    basename = "add_labeled_sample"

    @action(detail=False, methods=["post"])
    def add_labeled_sample(self, request, format=None):
        labeled_page = request.data["labeled_page"]
        freeze_software = request.data["freeze_software"]
        notes = request.data["notes"] if "notes" in request.data else ""
        labeled_sample_id = request.data.get("labeled_sample_id", None)

        # 1. Get the LabeledSample
        existing_labeled_sample = None
        try:
            if labeled_sample_id:
                existing_labeled_sample = LabeledSample.objects.get(
                    id=labeled_sample_id
                )
        except LabeledSample.DoesNotExist:
            pass

        if not existing_labeled_sample:
            # 2. If the LabeledSample does not exist create  first create the Sample
            sample = sample_from_required(labeled_page, freeze_software, notes)
            sample.save()
        else:
            # 2. Get the associated original sample.  Should always exist due to FK and cannot be Null
            sample = existing_labeled_sample.original_sample

        # 3. Create the new LabeledSample and save it.
        fta_sample, fta_ids_to_label = convert_fathom_sample_to_labeled_sample(
            labeled_page
        )
        labeled_sample, _ = LabeledSample.objects.get_or_create(
            original_sample=sample, modified_sample=fta_sample
        )

        # 4. If the sample did exist then update the superseded_by fields
        if existing_labeled_sample:
            LabeledSample.objects.filter(id=labeled_sample_id).update(
                superseded_by=labeled_sample.id
            )

        # 5. Create LabeledElements
        for fta_id, fathom_label in fta_ids_to_label.items():
            stored_label, created = Label.objects.get_or_create(slug=fathom_label)
            LabeledElement.objects.get_or_create(
                labeled_sample=labeled_sample,
                data_fta_id=fta_id,
                label=stored_label,
            )

        return Response({"id": sample.id})
