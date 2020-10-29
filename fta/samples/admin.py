from django.contrib import admin

from .models import Label, LabeledElement, LabeledSample, Sample


@admin.register(Sample)
class SampleAdmin(admin.ModelAdmin):
    list_display = ("id", "url", "page_size", "freeze_time", "freeze_software")


admin.site.register(Label)
admin.site.register(LabeledElement)
admin.site.register(LabeledSample)
