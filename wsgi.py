"""
WSGI config for Shareabouts Textizen adapter.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/
"""

# Import the project app to initialize the settings and view definitions
import app

# Create the WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# Send errors to Sentry
from raven.contrib.django.raven_compat.middleware.wsgi import Sentry
application = Sentry(application)
