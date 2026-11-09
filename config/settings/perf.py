"""Production settings over plain HTTP on localhost, for the Lighthouse CI job only."""

from .prod import *  # noqa: F403

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SERVE_MEDIA = True
