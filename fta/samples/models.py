from django.db import models


# Create your models here.
class Sample(models.Model):
    # We are using binary fields for simplicity for the time being.
    # May want to change to external storage later.

    # Required
    frozen_page = models.BinaryField(
        verbose_name="Blob of freeze-dried page",
        blank=False,
        editable=True,
    )
    url = models.URLField(
        verbose_name="Url or frozen page",
        max_length=1000,
    )
    freeze_time = models.DateTimeField(
        verbose_name="Time of page freezing",
    )
    # Optional
    notes = models.TextField(
        null=True,
        blank=True,
    )
    freeze_software = models.CharField(
        verbose_name="Software used for freezing",
        max_length=200,
        null=True,
        blank=True,
    )
