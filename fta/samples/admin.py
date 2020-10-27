from django.contrib import admin

from .models import Sample


@admin.register(Sample)
class SampleAdmin(admin.ModelAdmin):
    list_display = ("id", "url", "page_size", "freeze_time", "freeze_software")
