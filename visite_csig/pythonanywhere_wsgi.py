"""
WSGI config for PythonAnywhere deployment.

Copiez ce contenu dans Web > WSGI configuration file sur PythonAnywhere
"""

import os
import sys

path = '/home/Boubacar32/visite_csig'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
