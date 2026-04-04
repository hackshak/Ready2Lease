import uuid

from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import ListAPIView

from assessments.models import Assessment
from .models import TenantReport
from .serializers import TenantReportSerializer
from .services.action_plan_service import generate_actions
from .services.pdf_service import generate_pdf


class ReportsPageView(TemplateView):
    template_name = "reports/reports_page.html"


class ReportListView(ListAPIView):
    serializer_class = TenantReportSerializer

    def get_queryset(self):
        return TenantReport.objects.filter(
            assessment__user=self.request.user
        ).order_by("-created_at")


class GenerateTenantReport(APIView):

    def post(self, request, assessment_id):
        assessment = get_object_or_404(Assessment, id=assessment_id)

        # Always read the latest score — never recalculate it here.
        # AssessmentSubmitView owns the base score; action_plan views
        # update it whenever documents are uploaded / deleted.
        score     = assessment.readiness_score or 0
        strengths = assessment.strengths  or []
        risks     = assessment.weaknesses or []
        actions   = generate_actions(assessment)

        # update_or_create ensures re-generating for the same assessment
        # updates the existing record rather than creating a stale duplicate.
        report, created = TenantReport.objects.update_or_create(
            assessment=assessment,
            defaults={
                "score":     score,
                "strengths": strengths,
                "risks":     risks,
                "actions":   actions,
            }
        )

        # Assign a permanent report_id only on first creation.
        if created:
            report.report_id = f"R2L-{uuid.uuid4().hex[:10].upper()}"
            report.save(update_fields=["report_id"])

        # force_regenerate=True clears any cached PDF so the new score
        # and data are always reflected in the downloaded file.
        pdf_file = generate_pdf(report, force_regenerate=True)

        return Response({
            "report_id": report.report_id,
            "score":     score,
            "pdf":       pdf_file.url,
        })