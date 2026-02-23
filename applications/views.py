from django.shortcuts import render, redirect
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Application
from .serializers import ApplicationSerializer


# ==========================================================
# HELPER
# ==========================================================

def require_premium(user):
    return getattr(user, "is_premium", False)


# ==========================================================
# TEMPLATE PAGE VIEW (PREMIUM REQUIRED)
# ==========================================================

def application_page(request):
    if not request.user.is_authenticated:
        return redirect("login")

    if not require_premium(request.user):
        return redirect("dashboard_home")

    return render(request, "applications/applications.html")


# ==========================================================
# API VIEWSET (PREMIUM REQUIRED)
# ==========================================================

class ApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not require_premium(self.request.user):
            return Application.objects.none()

        return Application.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        if not require_premium(self.request.user):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Premium required")

        serializer.save(user=self.request.user)