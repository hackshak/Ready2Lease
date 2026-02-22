from django.urls import path
from .views import (
    AIAssistPageView,
    AIAssistChatView,
    UserAssessmentsView,
)

urlpatterns = [
    # Page
    path("", AIAssistPageView.as_view(), name="ai_assist_page"),

    # Chat API
    path("chat/", AIAssistChatView.as_view(), name="ai_chat"),

    # List Assessments API
    path("assessments/", UserAssessmentsView.as_view(), name="ai_user_assessments"),
]