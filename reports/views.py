import uuid

from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.views.generic import TemplateView

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import ListAPIView

from assessments.models import Assessment
from .models import TenantReport
from .serializers import TenantReportSerializer
from .services.scoring_service import calculate_score
from .services.analysis_service import generate_analysis
from .services.action_plan_service import generate_actions
from .services.pdf_service import generate_pdf

User = get_user_model()




class ReportsPageView(TemplateView):
    template_name = "reports/reports_page.html"



# REPORT LIST (ALL LOGGED-IN USERS)
class ReportListView(ListAPIView):
    serializer_class = TenantReportSerializer

    def get_queryset(self):
        return TenantReport.objects.filter(
            assessment__user=self.request.user
        ).order_by("-created_at")


# GENERATE TENANT REPORT
class GenerateTenantReport(APIView):

    def post(self, request, assessment_id):
        assessment = get_object_or_404(Assessment, id=assessment_id)

        score = calculate_score(assessment)

        assessment.save(update_fields=[
            "readiness_score",
            "risk_level",
            "strengths",
            "weaknesses",
            "recommendations",
            "gap_analysis",
        ])

        report = TenantReport.objects.create(
            assessment=assessment,
            report_id=f"R2L-{uuid.uuid4().hex[:10].upper()}",
            score=score,
            strengths=assessment.strengths,
            risks=assessment.weaknesses,
            actions=assessment.recommendations,
        )

        pdf_file = generate_pdf(report)

        return Response({
            "report_id": report.report_id,
            "score": score,
            "pdf": pdf_file.url,
        })