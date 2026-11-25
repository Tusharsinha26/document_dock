"""
URL configuration for documentdock project.
"""
import os
from pathlib import Path
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.utils._os import safe_join
from django.views.static import serve


def serve_media(request, path):
    """
    Serves repository media assets and (on Vercel temporary fallback) any uploads stored in /tmp.
    """
    if os.environ.get('VERCEL'):
        tmp_root = Path('/tmp/documentdock_media')
        try:
            candidate = Path(safe_join(str(tmp_root), path))
            if candidate.is_file():
                return serve(request, path, document_root=str(tmp_root))
        except Exception:
            pass
    return serve(request, path, document_root=settings.MEDIA_ROOT)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('vault.urls')),
    re_path(r'^media/(?P<path>.*)$', serve_media),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
