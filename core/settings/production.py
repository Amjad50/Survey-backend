from .common import *


DEBUG = False
ALLOWED_HOSTS = ["*"]

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", SECRET_KEY)
