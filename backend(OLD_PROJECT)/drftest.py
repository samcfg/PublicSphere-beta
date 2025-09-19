# drftest.py
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from rest_framework.settings import api_settings
print("Type of api_settings:", type(api_settings))
print("FORMAT_SUFFIX_KWARG:", getattr(api_settings, 'FORMAT_SUFFIX_KWARG', None))
print("EXCEPTION_HANDLER:", getattr(api_settings, 'EXCEPTION_HANDLER', None))