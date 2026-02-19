from django.urls import path
from .views import AIAssistChatView,AIAssistPageView

urlpatterns = [
    path("ai-assist/", AIAssistPageView.as_view(), name="ai_assist_page"),
    path("chat/", AIAssistChatView.as_view(), name="ai_chat"),
]

