from django.urls import path
from .views import (
    ReportsPageView,
    GenerateTenantReport,
    ReportListView
)

urlpatterns = [

    # frontend page
    path(
        "reports/",
        ReportsPageView.as_view(),
        name="reports"
    ),

    # list previous reports
    path(
        "list/",
        ReportListView.as_view(),
        name="report-list"
    ),

    # generate report
    path(
        "generate/<int:assessment_id>/",
        GenerateTenantReport.as_view(),
        name="generate-report"
    ),

]