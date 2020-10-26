from django.contrib import admin
from django.db import models

from .models import Sample


@admin.register(Sample)
class SampleAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.BinaryField: {"widget": admin.widgets.AdminTextareaWidget}
    }
