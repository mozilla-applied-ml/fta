from django.conf import settings as django_settings
from storages.backends.gcloud import GoogleCloudStorage


class StaticRootGoogleCloudStorage(GoogleCloudStorage):
    location = "static"
    default_acl = "publicRead"
    bucket_name = django_settings.GS_STATIC_BUCKET_NAME


class MediaRootGoogleCloudStorage(GoogleCloudStorage):
    file_overwrite = True
    bucket_name = django_settings.GS_MEDIA_BUCKET_NAME
