from django.urls import path
from . import views



urlpatterns = [
    path("dashboard/home/", views.dashboard_home, name="dashboard_home"),

    path("api/detailed-readiness/",
         views.DetailedReadinessAnalysisView.as_view(),
         name="detailed-readiness"),

    path("detailed-analysis/",
         views.detailed_analysis,
         name="detailed-analysis"),

    # ✅ LIST endpoint
    path(
        'api/calculate-detailed-analysis/',
        views.CalculateCategoryScoresView.as_view(),
        name='calculate_scores_list'
    ),

    # ✅ DETAIL endpoint
    path(
        'api/calculate-detailed-analysis/<int:assessment_id>/',
        views.CalculateCategoryScoresView.as_view(),
        name='calculate_scores'
    ),
]
