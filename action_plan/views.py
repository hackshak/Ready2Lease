from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction

from assessments.models import Assessment
from .services import ActionPlanService, TASK_POINTS
from .models import CompletedTask, UserDocument, ReferenceLetter, CoverLetter
from .checklist_service import ChecklistService


# ==========================================================
# HELPER
# ==========================================================

def require_premium(user):
    return getattr(user, "is_premium", False)


# ==========================================================
# PAGE VIEW
# ==========================================================

class ActionPlanPageView(LoginRequiredMixin, TemplateView):
    template_name = "action_plan/action_plan.html"

    def dispatch(self, request, *args, **kwargs):
        if not require_premium(request.user):
            return redirect("dashboard_home")
        return super().dispatch(request, *args, **kwargs)


# ==========================================================
# TASKS VIEW (PER ASSESSMENT)
# ==========================================================

class ActionPlanTasksView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, assessment_id=None):

        if not require_premium(request.user):
            return Response(
                {"detail": "Premium required"},
                status=status.HTTP_403_FORBIDDEN
            )

        if assessment_id:
            assessment = get_object_or_404(
                Assessment,
                id=assessment_id,
                user=request.user
            )
        else:
            assessment = ActionPlanService.get_latest_assessment(
                request.user
            )

        if not assessment:
            return Response({
                "tasks": [],
                "base_score": 0,
                "improvement_score": 0,
                "final_score": 0
            }, status=status.HTTP_200_OK)

        tasks = ActionPlanService.generate_tasks_for_assessment(
            assessment
        )

        return Response({
            "tasks": tasks,
            "base_score": assessment.readiness_score or 0,
            "improvement_score": ActionPlanService.get_improvement_score_for_assessment(
                assessment
            ),
            "final_score": ActionPlanService.get_final_score_for_assessment(
                request.user,
                assessment
            ),
        }, status=status.HTTP_200_OK)


# ==========================================================
# UPLOAD DOCUMENT (PER ASSESSMENT)
# ==========================================================

class UploadDocumentView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, assessment_id):

        if not require_premium(request.user):
            return Response(
                {"detail": "Premium required"},
                status=status.HTTP_403_FORBIDDEN
            )

        doc_type = request.data.get("document_type")
        file = request.FILES.get("file")

        if not file:
            return Response(
                {"detail": "File required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not doc_type:
            return Response(
                {"detail": "Document type required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        task_key = f"upload_{doc_type}"

        if task_key not in TASK_POINTS:
            return Response(
                {"detail": "Invalid document type"},
                status=status.HTTP_400_BAD_REQUEST
            )

        assessment = get_object_or_404(
            Assessment,
            id=assessment_id,
            user=request.user
        )

        UserDocument.objects.create(
            user=request.user,
            assessment=assessment,
            document_type=doc_type,
            file=file
        )

        CompletedTask.objects.get_or_create(
            user=request.user,
            assessment=assessment,
            task_key=task_key,
            defaults={"points_awarded": TASK_POINTS[task_key]}
        )

        return Response({
            "final_score": ActionPlanService.get_final_score_for_assessment(
                request.user,
                assessment
            )
        }, status=status.HTTP_200_OK)


# ==========================================================
# ADD REFERENCE (PER ASSESSMENT)
# ==========================================================

class AddReferenceView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, assessment_id):

        if not require_premium(request.user):
            return Response(
                {"detail": "Premium required"},
                status=status.HTTP_403_FORBIDDEN
            )

        file = request.FILES.get("file")
        text = request.data.get("text_content", "")

        if not file and not text:
            return Response(
                {"detail": "Reference file or text required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        assessment = get_object_or_404(
            Assessment,
            id=assessment_id,
            user=request.user
        )

        ReferenceLetter.objects.create(
            user=request.user,
            assessment=assessment,
            text_content=text,
            file=file
        )

        task_key = "add_reference_letter"

        if task_key in TASK_POINTS:
            CompletedTask.objects.get_or_create(
                user=request.user,
                assessment=assessment,
                task_key=task_key,
                defaults={"points_awarded": TASK_POINTS[task_key]}
            )

        return Response({
            "final_score": ActionPlanService.get_final_score_for_assessment(
                request.user,
                assessment
            )
        }, status=status.HTTP_200_OK)


# ==========================================================
# SAVE COVER LETTER (PER ASSESSMENT)
# ==========================================================

class SaveCoverLetterView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, assessment_id):

        if not require_premium(request.user):
            return Response(
                {"detail": "Premium required"},
                status=status.HTTP_403_FORBIDDEN
            )

        file = request.FILES.get("file")

        if not file:
            return Response(
                {"detail": "File is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        assessment = get_object_or_404(
            Assessment,
            id=assessment_id,
            user=request.user
        )

        CoverLetter.objects.update_or_create(
            user=request.user,
            assessment=assessment,
            defaults={"file": file}
        )

        task_key = "improve_cover_letter"

        if task_key in TASK_POINTS:
            CompletedTask.objects.get_or_create(
                user=request.user,
                assessment=assessment,
                task_key=task_key,
                defaults={"points_awarded": TASK_POINTS[task_key]}
            )

        return Response({
            "final_score": ActionPlanService.get_final_score_for_assessment(
                request.user,
                assessment
            )
        }, status=status.HTTP_200_OK)


# ==========================================================
# DOCUMENTS HOME PAGE
# ==========================================================

class DocumentsHomePageView(LoginRequiredMixin, TemplateView):
    template_name = "action_plan/documents.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["assessments"] = (
            Assessment.objects
            .filter(user=self.request.user)
            .order_by("-created_at")
        )
        return context


# ==========================================================
# DOCUMENT CHECKLIST API
# ==========================================================

class DocumentChecklistView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, assessment_id):

        assessment = get_object_or_404(
            Assessment,
            id=assessment_id,
            user=request.user
        )

        data = ChecklistService.get_checklist_for_assessment(
            request.user,
            assessment
        )

        return Response(data, status=status.HTTP_200_OK)


# ==========================================================
# DELETE DOCUMENT
# ==========================================================

class DeleteDocumentView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def delete(self, request, assessment_id, doc_type, object_id):

        assessment = get_object_or_404(
            Assessment,
            id=assessment_id,
            user=request.user
        )

        if doc_type in ["id_document", "payslip", "bank_statement"]:
            doc = get_object_or_404(
                UserDocument,
                id=object_id,
                user=request.user,
                assessment=assessment
            )
            doc.file.delete(save=False)
            doc.delete()

        elif doc_type == "reference_letter":
            ref = get_object_or_404(
                ReferenceLetter,
                id=object_id,
                user=request.user,
                assessment=assessment
            )
            if ref.file:
                ref.file.delete(save=False)
            ref.delete()

        elif doc_type == "cover_letter":
            cover = get_object_or_404(
                CoverLetter,
                id=object_id,
                user=request.user,
                assessment=assessment
            )
            cover.delete()

        else:
            return Response(
                {"detail": "Invalid document type"},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {"detail": "Deleted successfully"},
            status=status.HTTP_200_OK
        )