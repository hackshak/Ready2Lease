import uuid

from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from assessments.models import Assessment
from .models import TenantReport

from .services.scoring_service import calculate_score
from .services.analysis_service import generate_analysis
from .services.action_plan_service import generate_actions
from .services.pdf_service import generate_pdf
from django.views.generic import TemplateView

from rest_framework.generics import ListAPIView
from .serializers import TenantReportSerializer



class ReportsPageView(TemplateView):
    template_name = "reports/reports_page.html"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context["is_premium"] = getattr(self.request.user, "is_premium", False)

        return context





class ReportListView(ListAPIView):

    serializer_class = TenantReportSerializer

    def get_queryset(self):

        user = self.request.user

        return TenantReport.objects.filter(
            assessment__user=user
        ).order_by("-created_at")
    




class GenerateTenantReport(APIView):

    def post(self, request, assessment_id):

        assessment = get_object_or_404(Assessment, id=assessment_id)

        score = calculate_score(assessment)

        strengths, risks = generate_analysis(assessment)

        actions = generate_actions(assessment)

        report = TenantReport.objects.create(
            assessment=assessment,
            report_id=f"assess_{uuid.uuid4().hex[:12]}",
            score=score,
            strengths=strengths,
            risks=risks,
            actions=actions
        )

        pdf_file = generate_pdf(report)

        return Response({
            "report_id": report.report_id,
            "pdf": pdf_file.url
        })