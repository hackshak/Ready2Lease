from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListAPIView

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect

from .models import AIAssistMessage
from .serializers import AIAssistMessageSerializer
from .services import generate_ai_response

from assessments.models import Assessment
from assessments.serializers import AssessmentSerializer


class AIAssistPageView(LoginRequiredMixin, TemplateView):
    template_name = "ai_assist/ai_assist.html"

    def dispatch(self, request, *args, **kwargs):
        # Premium Gate
        if not request.user.is_premium:
            return redirect("dashboard_home")
        return super().dispatch(request, *args, **kwargs)


# ✅ NEW: List all assessments for logged-in user
class UserAssessmentsView(ListAPIView):
    serializer_class = AssessmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Assessment.objects.filter(
            user=self.request.user
        ).order_by("-created_at")


# ✅ Updated Chat View
class AIAssistChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_message = request.data.get("message", "").strip()
        assessment_id = request.data.get("assessment_id")
        history = request.data.get("history", [])

        if not user_message:
            return Response({"detail": "Message required"}, status=400)

        if not assessment_id:
            return Response({"detail": "Assessment selection required"}, status=400)

        try:
            assessment = Assessment.objects.get(
                id=assessment_id,
                user=request.user
            )
        except Assessment.DoesNotExist:
            return Response({"detail": "Invalid assessment"}, status=400)

        # Generate AI response (no DB save)
        ai_reply = generate_ai_response(
            user=request.user,
            history=history,
            assessment=assessment
        )

        return Response({"reply": ai_reply})