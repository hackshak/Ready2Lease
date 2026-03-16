from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from .models import Application
from .serializers import ApplicationSerializer

User = get_user_model()


# HELPER — always reads fresh from DB, never the session cache
def require_premium(user):
    """
    Re-fetches the user from the DB on every call so we never
    read a stale is_premium value from the Django session cache.
    """
    try:
        fresh = User.objects.get(pk=user.pk)
        return fresh.is_premium
    except User.DoesNotExist:
        return False


def application_page(request):
    if not request.user.is_authenticated:
        return redirect("login")

    return render(request, "applications/applications.html")


# API VIEWSET (FUNCTIONALITY → PREMIUM ONLY)
class ApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not require_premium(self.request.user):
            return Application.objects.none()

        return Application.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        if not require_premium(self.request.user):
            raise PermissionDenied("Premium required")

        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        if not require_premium(self.request.user):
            raise PermissionDenied("Premium required")

        serializer.save()

    def perform_destroy(self, instance):
        if not require_premium(self.request.user):
            raise PermissionDenied("Premium required")

        instance.delete()