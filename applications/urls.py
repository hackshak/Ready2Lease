from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ApplicationViewSet, application_page

# DRF Router for CRUD API
router = DefaultRouter()
router.register(r'applications', ApplicationViewSet, basename='applications')

urlpatterns = [
    # Template Page
    path('applications/', application_page, name='application_page'),

    # API Routes
    path('api/', include(router.urls)),
]