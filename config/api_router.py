from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from fta.samples.api.views import SampleViewSet

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

# Example how to register
router.register("samples", SampleViewSet)


app_name = "api"
urlpatterns = router.urls
