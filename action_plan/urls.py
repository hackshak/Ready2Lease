from django.urls import path
from .views import (
    ActionPlanTasksView,
    UploadDocumentView,
    AddReferenceView,
    SaveCoverLetterView,
    ActionPlanPageView,
    DocumentChecklistView,
    DeleteDocumentView,
    DocumentsHomePageView
)

urlpatterns = [

    # Action Plan Page
    path(
        "action-plan/",
        ActionPlanPageView.as_view(),
        name="action_plan_page"
    ),

    # Tasks for specific assessment
    path(
        "tasks/<int:assessment_id>/",
        ActionPlanTasksView.as_view(),
        name="action_plan_tasks"
    ),

    # Fallback (latest assessment)
    path(
        "tasks/",
        ActionPlanTasksView.as_view(),
        name="action_plan_tasks_latest"
    ),

    # Upload document for selected assessment
    path(
        "upload-document/<int:assessment_id>/",
        UploadDocumentView.as_view(),
        name="upload_document"
    ),

    # Add reference for selected assessment
    path(
        "add-reference/<int:assessment_id>/",
        AddReferenceView.as_view(),
        name="add_reference"
    ),

    # Save cover letter for selected assessment
    path(
        "save-cover-letter/<int:assessment_id>/",
        SaveCoverLetterView.as_view(),
        name="save_cover_letter"
    ),
    path(
        "documents/",
        DocumentsHomePageView.as_view(),
        name="document_home"
    ),
    path(
        "checklist/<int:assessment_id>/",
        DocumentChecklistView.as_view(),
        name="document_checklist"
    ),
    path(
        "checklist/<int:assessment_id>/delete/<str:doc_type>/<int:object_id>/",
        DeleteDocumentView.as_view(),
        name="delete_document"
    ),
]




