import os

from .base import *  # noqa
from .base import env

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env("DJANGO_SECRET_KEY")
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
if os.getenv("GAE_INSTANCE"):
    # App Engine's security features ensure that it is safe to have ALLOWED_HOSTS = ['*'] when the app is deployed.
    # Source:
    # https://github.com/GoogleCloudPlatform/python-docs-samples/blob/master/appengine/flexible/django_cloudsql/mysite/settings.py#L30  # noqa
    ALLOWED_HOSTS = ["*"]
else:
    ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["example.com"])

# DATABASES
# ------------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env.str("DB_NAME"),
        "USER": env.str("DB_USERNAME"),
        "PASSWORD": env.str("DB_PASSWORD"),
        "HOST": f'/cloudsql/{env.str("CLOUD_SQL_INSTANCE_ID")}',
        "ATOMIC_REQUESTS": True,
        "CONN_MAX_AGE": env.int("CONN_MAX_AGE", default=60),
        "PORT": "5432",
    },
}
if os.getenv("GAE_INSTANCE"):
    pass
else:
    DATABASES["default"]["HOST"] = "127.0.0.1"
    DATABASES["default"]["PORT"] = "5454"


# SECURITY
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-proxy-ssl-header
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-ssl-redirect
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
# https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-secure
SESSION_COOKIE_SECURE = True
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-secure
CSRF_COOKIE_SECURE = True
# https://docs.djangoproject.com/en/dev/topics/security/#ssl-https
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-seconds
# TODO: set this to 60 seconds first and then to 518400 once you prove the former works
SECURE_HSTS_SECONDS = 60
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-include-subdomains
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool(
    "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True
)
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-preload
SECURE_HSTS_PRELOAD = env.bool("DJANGO_SECURE_HSTS_PRELOAD", default=True)
# https://docs.djangoproject.com/en/dev/ref/middleware/#x-content-type-options-nosniff
SECURE_CONTENT_TYPE_NOSNIFF = env.bool(
    "DJANGO_SECURE_CONTENT_TYPE_NOSNIFF", default=True
)

#
# FOR NOW BEING LAZY AND USING BUILT IN STATIC FILE SERVING.
# THIS IS NOT A PRODUCTION QUALITY SOLUTION, BUT IT'S AN INTERNAL WEB APP.
#

# STORAGES
# ------------------------------------------------------------------------------
#
# https://django-storages.readthedocs.io/en/latest/#installation
INSTALLED_APPS += ["storages"]  # noqa F405

# STATIC
# ------------------------
GS_STATIC_BUCKET_NAME = env("DJANGO_GCP_STORAGE_BUCKET_NAME")
STATICFILES_STORAGE = "fta.utils.storages.StaticRootGoogleCloudStorage"
STATIC_URL = f"https://{GS_STATIC_BUCKET_NAME}.storage.googleapis.com/{GS_STATIC_BUCKET_NAME}/static/"
CORS_ALLOWED_ORIGINS = [f"https://{GS_STATIC_BUCKET_NAME}.storage.googleapis.com"]

# MEDIA
# ------------------------------------------------------------------------------
GS_MEDIA_BUCKET_NAME = env("DJANGO_GCP_MEDIA_BUCKET_NAME")
DEFAULT_FILE_STORAGE = "fta.utils.storages.MediaRootGoogleCloudStorage"
MEDIA_URL = (
    f"https://{GS_MEDIA_BUCKET_NAME}.storage.googleapis.com/{GS_MEDIA_BUCKET_NAME}/"
)


# EMAIL
#
# NOT DOING EMAIL FOR NOW - Error reporting via dashboard
#
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#default-from-email
# DEFAULT_FROM_EMAIL = env(
#    "DJANGO_DEFAULT_FROM_EMAIL", default="FTA <noreply@example.com>"
# )
# https://docs.djangoproject.com/en/dev/ref/settings/#server-email
# SERVER_EMAIL = env("DJANGO_SERVER_EMAIL", default=DEFAULT_FROM_EMAIL)
# https://docs.djangoproject.com/en/dev/ref/settings/#email-subject-prefix
# EMAIL_SUBJECT_PREFIX = env("DJANGO_EMAIL_SUBJECT_PREFIX", default="[FTA]")

# ADMIN
# ------------------------------------------------------------------------------
# Django Admin URL regex.
# ADMIN_URL = env("DJANGO_ADMIN_URL")

# Anymail
# ------------------------------------------------------------------------------
# https://anymail.readthedocs.io/en/stable/installation/#installing-anymail
# INSTALLED_APPS += ["anymail"]  # noqa F405

# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
# https://anymail.readthedocs.io/en/stable/installation/#anymail-settings-reference
# https://anymail.readthedocs.io/en/stable/esps/mailgun/
# EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"
# ANYMAIL = {
#    "MAILGUN_API_KEY": env("MAILGUN_API_KEY"),
#    "MAILGUN_SENDER_DOMAIN": env("MAILGUN_DOMAIN"),
#    "MAILGUN_API_URL": env("MAILGUN_API_URL", default="https://api.mailgun.net/v3"),
# }

# LOGGING
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#logging
# See https://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
#
# For now, we'll just rely on google dashboard for reporting
#
# LOGGING = {
#    "version": 1,
#    "disable_existing_loggers": False,
#    "filters": {"require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}},
#    "formatters": {
#        "verbose": {
#            "format": "%(levelname)s %(asctime)s %(module)s "
#            "%(process)d %(thread)d %(message)s"
#        }
#    },
#    "handlers": {
#        "mail_admins": {
#            "level": "ERROR",
#            "filters": ["require_debug_false"],
#            "class": "django.utils.log.AdminEmailHandler",
#        },
#        "console": {
#            "level": "DEBUG",
#            "class": "logging.StreamHandler",
#            "formatter": "verbose",
#        },
#    },
#    "root": {"level": "INFO", "handlers": ["console"]},
#    "loggers": {
#        "django.request": {
#            "handlers": ["mail_admins"],
#            "level": "ERROR",
#            "propagate": True,
#        },
#        "django.security.DisallowedHost": {
#            "level": "ERROR",
#            "handlers": ["console", "mail_admins"],
#            "propagate": True,
#        },
#    },
# }

# Your stuff...
# ------------------------------------------------------------------------------
