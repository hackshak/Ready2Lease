from django.urls import path
from .views import (
    ActionPlanTasksView,
    UploadDocumentView,
    AddReferenceView,
    SaveCoverLetterView,
    ActionPlanPageView
)

urlpatterns = [
    path("action-plan/", ActionPlanPageView.as_view(), name="action_plan_page"),
    path("tasks/", ActionPlanTasksView.as_view()),
    path("upload-document/", UploadDocumentView.as_view()),
    path("add-reference/", AddReferenceView.as_view()),
    path("save-cover-letter/", SaveCoverLetterView.as_view()),
]
