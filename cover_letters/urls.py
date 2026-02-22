# cover_letters/urls.py

from django.urls import path
from .views import (
    cover_letter_list_view,
    cover_letter_editor_view,
    CoverLetterListAPI,
    GenerateCoverLetterAPI,
    CoverLetterDetailAPI,
    SaveCoverLetterAPI,
    ExportCoverLetterPDFAPI,
)


urlpatterns = [

    # ============================
    # TEMPLATE VIEWS
    # ============================

    path(
        "cover-letters/",
        cover_letter_list_view,
        name="cover_letter_list",
    ),

    path(
        "cover-letters/<int:pk>/",
        cover_letter_editor_view,
        name="cover_letter_editor",
    ),

    # ============================
    # API ENDPOINTS
    # ============================

    path(
        "api/cover-letters/",
        CoverLetterListAPI.as_view(),
        name="api_cover_letter_list",
    ),

    path(
        "api/cover-letters/generate/",
        GenerateCoverLetterAPI.as_view(),
        name="api_generate_cover_letter",
    ),

    path(
        "api/cover-letters/<int:pk>/",
        CoverLetterDetailAPI.as_view(),
        name="api_cover_letter_detail",
    ),

    path(
        "api/cover-letters/<int:pk>/save/",
        SaveCoverLetterAPI.as_view(),
        name="api_save_cover_letter",
    ),

    path(
        "api/cover-letters/<int:pk>/export/",
        ExportCoverLetterPDFAPI.as_view(),
        name="api_export_cover_letter",
    ),
]