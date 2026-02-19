from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import AIAssistMessage
from .serializers import AIAssistMessageSerializer
from .services import generate_ai_response
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin




class AIAssistPageView(LoginRequiredMixin, TemplateView):
    template_name = "ai_assist/ai_assist.html"

    def dispatch(self, request, *args, **kwargs):
        # Optional: Premium Gate
        if not request.user.is_premium:
            from django.shortcuts import redirect
            return redirect("dashboard_home")
        return super().dispatch(request, *args, **kwargs)



class AIAssistChatView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        messages = request.user.ai_messages.all()
        serializer = AIAssistMessageSerializer(messages, many=True)
        return Response(serializer.data)

    def post(self, request):
        user_message = request.data.get("message", "").strip()

        if not user_message:
            return Response({"detail": "Message required"}, status=400)

        # Save user message
        user_msg = AIAssistMessage.objects.create(
            user=request.user,
            role="user",
            content=user_message
        )

        # Get last 8 messages for context
        history = request.user.ai_messages.order_by("-created_at")[:8]
        history = list(reversed(history))

        # Generate AI response
        ai_reply = generate_ai_response(request.user, history)

        assistant_msg = AIAssistMessage.objects.create(
            user=request.user,
            role="assistant",
            content=ai_reply
        )

        return Response({
            "reply": assistant_msg.content
        })