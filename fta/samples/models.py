from django.db import models

# These are the freezers we know how to parse the meta data from
SAMPLE_SOFTWARE_PARSERS = (("SinglePage", "SinglePage"), ("freezedry", "freezedry"))


# Create your models here.
class Sample(models.Model):
    # We are using binary fields for simplicity for the time being.
    # May want to change to external storage later.

    # Required
    frozen_page = models.TextField(
        verbose_name="Freeze-dried page",
        blank=False,
        max_length=None,
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
    page_size = models.IntegerField(
        verbose_name="Page size",
        help_text="This is updated on save, don't bother manually changing.",
        blank=True,
        null=True,
    )

    def save(self, *args, **kwargs):
        self.page_size = len(self.frozen_page.encode("utf-8"))
        super().save(*args, **kwargs)
