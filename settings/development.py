"""Development settings and globals."""
from __future__ import absolute_import

from .base import *


INSTALLED_APPS = INSTALLED_APPS + [
    'django_extensions',  # More & better manage.py commands
]
