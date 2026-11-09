from .base import *  # noqa: F403
from .base import BASE_DIR

ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
MEDIA_ROOT = BASE_DIR / ".test-media"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
SERVE_MEDIA = True
# WhiteNoise serves straight from the source folders, so collectstatic is not needed.
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = True
