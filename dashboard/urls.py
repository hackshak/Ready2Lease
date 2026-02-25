from django.urls import path
from . import views

urlpatterns = [

    path("dashboard/home/", views.dashboard_home, name="dashboard_home"),
    path("detailed-analysis/", views.detailed_analysis, name="detailed-analysis"),

    # FREE API
    path(
        "api/free-readiness/",
        views.FreeReadinessView.as_view(),
        name="free-readiness"
    ),

    # PREMIUM API
    path(
        "api/detailed-readiness/",
        views.DetailedReadinessAnalysisView.as_view(),
        name="detailed-readiness"
    ),

    path(
        "api/detailed-readiness/<int:assessment_id>/",
        views.DetailedReadinessAnalysisView.as_view(),
        name="detailed-readiness-detail"
    ),

    # Premium scoring
    path(
        'api/calculate-detailed-analysis/',
        views.CalculateCategoryScoresView.as_view(),
        name='calculate_scores_list'
    ),

    path(
        'api/calculate-detailed-analysis/<int:assessment_id>/',
        views.CalculateCategoryScoresView.as_view(),
        name='calculate_scores'
    ),
]