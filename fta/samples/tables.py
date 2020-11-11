import django_tables2 as tables
from django.template.defaultfilters import truncatechars
from django.utils.html import format_html
from django_tables2.utils import A

from .models import Sample
from .utils import humansize


class SampleTable(tables.Table):
    edit = tables.LinkColumn(
        "label", text="Edit Labels", args=[A("pk")], orderable=False
    )
    labels = tables.Column(accessor="pk", orderable=True)

    class Meta:
        model = Sample
        template_name = "django_tables2/bootstrap4.html"
        attrs = {"class": "table table-sm table-bordered"}
        fields = (
            "edit",
            "labels",
            "url",
            "freeze_time",
            "freeze_software",
            "page_size",
            "notes",
        )

    def render_labels(self, value, record):
        default = format_html('<a href="?label=-">-</a>')
        if hasattr(record, "labeled_sample"):
            labeled_elements = record.labeled_sample.labeled_elements.all()
            labels = labeled_elements.values_list("label__slug", flat=True).distinct()
            if labels:
                label_links = [
                    f'<a href="?label={label}">{label}</a>' for label in labels
                ]
                return format_html(", ".join(label_links))
        return default

    def order_labels(self, queryset, is_descending):
        queryset = queryset.order_by(("-" if is_descending else "") + "nlabels")
        return (queryset, True)

    def render_page_size(self, value, record):
        return humansize(value)

    def render_url(self, value, record):
        return f"{truncatechars(value, 80)}"
