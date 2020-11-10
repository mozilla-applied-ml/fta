from django.db import models
from django.dispatch import receiver

# These are the freezers we know how to parse the meta data from
SAMPLE_SOFTWARE_PARSERS = (("SingleFile", "SingleFile"), ("freezedry", "freezedry"))


class SampleManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("labeled_sample")
            .prefetch_related("labeled_sample__labeled_elements")
            .annotate(nlabels=models.Count("labeled_sample__labeled_elements"))
        )


# Create your models here.
class Sample(models.Model):
    # We are using binary fields for simplicity for the time being.
    # May want to change to external storage later.

    objects = SampleManager()

    # Required
    frozen_page = models.TextField(
        verbose_name="Frozen page",
        blank=False,
        max_length=None,
    )
    url = models.URLField(
        verbose_name="Url of frozen page",
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
    page_width = models.IntegerField(
        verbose_name="Page width in pixels", blank=True, null=True
    )
    page_height = models.IntegerField(
        verbose_name="Page height in pixels", blank=True, null=True
    )

    def save(self, *args, **kwargs):
        self.page_size = len(self.frozen_page.encode("utf-8"))
        super().save(*args, **kwargs)


@receiver(models.signals.pre_save, sender=Sample)
def prevent_updating_of_frozen_page_and_data(sender, instance, **kwargs):
    try:
        obj = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        pass  # Initial save -- do nothing
    else:
        if (
            (obj.frozen_page != instance.frozen_page)
            or (obj.url != instance.url)
            or (obj.freeze_time != instance.freeze_time)
            or (obj.freeze_software != instance.freeze_software)
        ):
            raise models.ProtectedError(
                "Only notes can be changed after initial creation."
            )


class LabeledSample(models.Model):
    original_sample = models.OneToOneField(
        Sample,
        related_name="labeled_sample",
        on_delete=models.CASCADE,
        blank=False,
        null=False,
        help_text="Link to the original sample",
    )
    modified_sample = models.TextField(
        help_text="Sample page modified with labeling ids. This is mutable.",
        blank=False,
        max_length=None,
    )

    def __str__(self):
        return f"{self.original_sample.pk} - {self.original_sample.url}"


class Label(models.Model):
    slug = models.SlugField(
        blank=False,
        null=False,
        help_text="data-fathom - This is the slug that populates data-fathom.",
        unique=True,
    )
    description = models.TextField(
        blank=True, null=True, help_text="Description of label."
    )

    def __str__(self):
        return self.slug


class LabeledElement(models.Model):
    labeled_sample = models.ForeignKey(
        to=LabeledSample,
        related_name="labeled_elements",
        on_delete=models.CASCADE,
        blank=False,
        null=False,
        help_text="Link to labeled sample",
    )
    data_fta_id = models.SlugField(
        max_length=64,
        blank=False,
        null=False,
        help_text="data-fta_id - This is the id in the Labeled Sample.",
    )
    label = models.ForeignKey(
        to=Label,
        on_delete=models.CASCADE,
        blank=False,
        null=False,
        help_text="data-fta_id - This is the id in the Labeled Sample.",
    )

    class Meta:
        # Can't have more than one label for a field
        unique_together = ["data_fta_id", "labeled_sample"]

    def __str__(self):
        return f"{self.labeled_sample.pk} - {self.label} - {self.data_fta_id}"
