from datetime import datetime
from uuid import uuid4

from django.conf import settings
from django.contrib import admin, messages
from django.core.files.base import ContentFile
from django.core.files.storage import get_storage_class
from django.template.defaultfilters import truncatechars

from .models import Label, LabeledElement, LabeledSample, Sample
from .utils import convert_labeled_sample_to_fathom_sample, humansize


@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    list_display = ("slug", "description")


@admin.register(LabeledElement)
class LabeledElementAdmin(admin.ModelAdmin):
    list_display = ("id", "labeled_sample", "label", "data_fta_id")


@admin.register(Sample)
class SampleAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "pretty_page_size",
        "truncated_url",
        "freeze_time",
        "freeze_software",
    )

    def pretty_page_size(self, obj):
        return humansize(obj.page_size)

    pretty_page_size.short_description = "Page Size"
    pretty_page_size.admin_order_field = "page_size"

    def truncated_url(self, obj):
        return truncatechars(obj.url, 140)

    truncated_url.short_description = "Url"
    truncated_url.admin_order_field = "url"


class PageSizeListFilter(admin.SimpleListFilter):
    title = "page size"
    parameter_name = "page_size"

    def lookups(self, request, model_admin):
        return (
            ("1048576", "<1MB"),
            ("10485760", "<10MB"),
        )

    def queryset(self, request, queryset):
        val = self.used_parameters.get("page_size")
        if val:
            queryset = queryset.filter(original_sample__page_size__lte=val)
        return queryset


class LabelListFilter(admin.SimpleListFilter):
    title = "label"
    parameter_name = "label"

    def lookups(self, request, model_admin):
        labels = LabeledElement.objects.distinct("label").values_list(
            "label__slug", flat=True
        )
        return [(slug, slug) for slug in labels]

    def queryset(self, request, queryset):
        val = self.used_parameters.get("label")
        if val:
            queryset = queryset.filter(labeled_elements__label__slug=val)
        return queryset


@admin.register(LabeledSample)
class LabeledSampleAdmin(admin.ModelAdmin):
    list_select_related = True

    # Search - only filters labels
    search_fields = ["labeled_elements__label__slug"]

    def get_search_results(self, request, queryset, search_term):
        # See: https://docs.djangoproject.com/en/3.1/ref/contrib/admin/#django.contrib.admin.ModelAdmin.get_search_results # noqa
        use_distinct = True
        if search_term:
            slug_fields = [x.strip() for x in search_term.split(",")]
            queryset = queryset.filter(labeled_elements__label__slug__in=slug_fields)
        return queryset, use_distinct

    # Export actions
    actions = [
        "export_labeled_samples",
    ]

    def export_labeled_samples(self, request, queryset):
        storage_class = get_storage_class()
        storage = storage_class()
        folder = f"{datetime.now():%Y-%m-%d}-{str(uuid4())[0:6]}"
        for sample in queryset:
            processed_sample = convert_labeled_sample_to_fathom_sample(sample)
            storage.save(
                name=f"{folder}/{sample.pk}", content=ContentFile(processed_sample)
            )

        self.message_user(
            request,
            f"Samples were exported to {settings.MEDIA_URL}/{folder}",
            messages.SUCCESS,
        )

    export_labeled_samples.short_description = "Export selected samples as fathom set"

    # Filters
    list_filter = (
        "original_sample__freeze_software",
        "original_sample__freeze_time",
        PageSizeListFilter,
        LabelListFilter,
    )

    # Display
    list_display = (
        "id",
        "nlabels",
        "labels",
        "page_size",
        "url",
        "freeze_time",
        "freeze_software",
    )

    def nlabels(self, obj):
        return obj.nlabels

    nlabels.admin_order_field = "nlabels"
    nlabels.short_description = "N labels"

    def labels(self, obj):
        return ", ".join(
            obj.labeled_elements.all().values_list("label__slug", flat=True)
        )

    def page_size(self, obj):
        return humansize(obj.original_sample.page_size)

    page_size.admin_order_field = "original_sample__page_size"

    def url(self, obj):
        return truncatechars(obj.original_sample.url, 140)

    url.admin_order_field = "url"

    def freeze_time(self, obj):
        return obj.original_sample.freeze_time

    def freeze_software(self, obj):
        return obj.original_sample.freeze_software
