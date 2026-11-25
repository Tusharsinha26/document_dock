"""
WSGI config for documentdock project.

It exposes the WSGI callable as a module-level variable named ``application``
(and ``app`` alias for serverless runtimes such as Vercel).
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'documentdock.settings')

application = get_wsgi_application()
app = application
