from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from fta.samples.api.views import (
    AddLabeledSampleViewSet,
    AddSampleViewSet,
    SampleViewSet,
)

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

# Example how to register
router.register("samples", SampleViewSet)
router.register("add_sample", AddSampleViewSet, basename="add_sample")
router.register(
    "add_labeled_sample", AddLabeledSampleViewSet, basename="add_labeled_sample"
)


app_name = "api"
urlpatterns = router.urls
