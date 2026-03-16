"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),

    path('', include('core.urls')),
    path('auth/', include('users.urls')),

    path('', include('assessments.urls')),
    path('', include('dashboard.urls')),
    path('', include('action_plan.urls')),

    path('', include('applications.urls')),
    path("", include("cover_letters.urls")),

    path('payments/', include('payments.urls')),

    path("", include("reports.urls")),
    path("", include("blog.urls")),
]


# Serve media files during development only
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)