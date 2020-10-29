from django.contrib import admin

from .models import Label, LabeledElement, LabeledSample, Sample


@admin.register(Sample)
class SampleAdmin(admin.ModelAdmin):
    list_display = ("id", "url", "page_size", "freeze_time", "freeze_software")


@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    list_display = ("slug", "description")


@admin.register(LabeledElement)
class LabeledElementAdmin(admin.ModelAdmin):
    list_display = ("labeled_sample", "label", "data_fta_id")


admin.site.register(LabeledSample)
