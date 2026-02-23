from django.shortcuts import render, redirect
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from .models import Application
from .serializers import ApplicationSerializer


# ==========================================================
# HELPER
# ==========================================================

def require_premium(user):
    return getattr(user, "is_premium", False)


# ==========================================================
# TEMPLATE PAGE VIEW (VISIBLE TO ALL LOGGED-IN USERS)
# ==========================================================

def application_page(request):
    if not request.user.is_authenticated:
        return redirect("login")

    # ✅ Page visible to all logged-in users
    return render(
        request,
        "applications/applications.html",
        {
            "is_premium": require_premium(request.user)
        }
    )


# ==========================================================
# API VIEWSET (FUNCTIONALITY → PREMIUM ONLY)
# ==========================================================

class ApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Non-premium users cannot access application data
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