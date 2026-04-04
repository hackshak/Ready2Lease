from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.db import transaction

from assessments.models import Assessment
from .services import ActionPlanService, TASK_WEIGHTS
from .models import CompletedTask, UserDocument, ReferenceLetter, CoverLetter
from .checklist_service import ChecklistService

User = get_user_model()


def require_premium(user):
    try:
        fresh = User.objects.get(pk=user.pk)
        return fresh.is_premium
    except User.DoesNotExist:
        return False


class ActionPlanPageView(LoginRequiredMixin, TemplateView):
    template_name = "action_plan/action_plan.html"


class ActionPlanTasksView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, assessment_id=None):
        if not require_premium(request.user):
            return Response({"detail": "Premium required"}, status=status.HTTP_403_FORBIDDEN)

        if assessment_id:
            assessment = get_object_or_404(Assessment, id=assessment_id, user=request.user)
        else:
            assessment = ActionPlanService.get_latest_assessment(request.user)

        if not assessment:
            return Response({
                "tasks": [],
                "base_score": 0,
                "improvement_score": 0,
                "final_score": 0
            })

        tasks = ActionPlanService.generate_tasks_for_assessment(assessment)
        final_score = ActionPlanService.get_final_score_for_assessment(request.user, assessment)

        return Response({
            "tasks": tasks,
            "base_score": assessment.readiness_score or 0,
            "improvement_score": ActionPlanService.get_improvement_score_for_assessment(assessment),
            "final_score": final_score,
        })


class UploadDocumentView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, assessment_id):
        if not require_premium(request.user):
            return Response({"detail": "Premium required"}, status=status.HTTP_403_FORBIDDEN)

        doc_type = request.data.get("document_type")
        file = request.FILES.get("file")

        if not file or not doc_type:
            return Response({"detail": "File and document_type required"}, status=status.HTTP_400_BAD_REQUEST)

        task_key = f"upload_{doc_type}"
        if task_key not in TASK_WEIGHTS:
            return Response({"detail": "Invalid document type"}, status=status.HTTP_400_BAD_REQUEST)

        assessment = get_object_or_404(Assessment, id=assessment_id, user=request.user)

        # Create document
        UserDocument.objects.create(
            user=request.user,
            assessment=assessment,
            document_type=doc_type,
            file=file
        )

        # Calculate points for this task at current state
        all_tasks = ActionPlanService.get_all_possible_tasks(assessment)
        existing_completed = set(
            CompletedTask.objects.filter(user=request.user, assessment=assessment)
            .values_list("task_key", flat=True)
        )
        tasks_to_scale = [t for t in all_tasks if t["key"] not in existing_completed]
        scaled = ActionPlanService.scale_task_points(assessment, tasks_to_scale)
        points_earned = 0
        for task in scaled:
            if task["key"] == task_key:
                points_earned = task.get("points", 0)
                break

        # Mark task as completed with earned points
        CompletedTask.objects.get_or_create(
            user=request.user,
            assessment=assessment,
            task_key=task_key,
            defaults={"points_earned": points_earned}
        )

        # ✅ NEW SCORE = old score + points earned (capped at 100)
        old_score = assessment.readiness_score or 0
        new_score = min(old_score + points_earned, 100)
        assessment.readiness_score = new_score
        assessment.save(update_fields=["readiness_score"])

        return Response({"final_score": new_score}, status=status.HTTP_200_OK)


class AddReferenceView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, assessment_id):
        if not require_premium(request.user):
            return Response({"detail": "Premium required"}, status=status.HTTP_403_FORBIDDEN)

        file = request.FILES.get("file")
        if not file:
            return Response({"detail": "Reference file required"}, status=status.HTTP_400_BAD_REQUEST)

        assessment = get_object_or_404(Assessment, id=assessment_id, user=request.user)

        ReferenceLetter.objects.create(
            user=request.user,
            assessment=assessment,
            file=file
        )

        task_key = "add_reference_letter"
        existing_completed = set(
            CompletedTask.objects.filter(user=request.user, assessment=assessment)
            .values_list("task_key", flat=True)
        )
        all_tasks = ActionPlanService.get_all_possible_tasks(assessment)
        tasks_to_scale = [t for t in all_tasks if t["key"] not in existing_completed]
        scaled = ActionPlanService.scale_task_points(assessment, tasks_to_scale)
        points_earned = 0
        for task in scaled:
            if task["key"] == task_key:
                points_earned = task.get("points", 0)
                break

        CompletedTask.objects.get_or_create(
            user=request.user,
            assessment=assessment,
            task_key=task_key,
            defaults={"points_earned": points_earned}
        )

        old_score = assessment.readiness_score or 0
        new_score = min(old_score + points_earned, 100)
        assessment.readiness_score = new_score
        assessment.save(update_fields=["readiness_score"])

        return Response({"final_score": new_score}, status=status.HTTP_200_OK)


class SaveCoverLetterView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, assessment_id):
        if not require_premium(request.user):
            return Response({"detail": "Premium required"}, status=status.HTTP_403_FORBIDDEN)

        file = request.FILES.get("file")
        if not file:
            return Response({"detail": "File required"}, status=status.HTTP_400_BAD_REQUEST)

        assessment = get_object_or_404(Assessment, id=assessment_id, user=request.user)

        CoverLetter.objects.update_or_create(
            user=request.user,
            assessment=assessment,
            defaults={"file": file}
        )

        task_key = "improve_cover_letter"
        existing_completed = set(
            CompletedTask.objects.filter(user=request.user, assessment=assessment)
            .values_list("task_key", flat=True)
        )
        all_tasks = ActionPlanService.get_all_possible_tasks(assessment)
        tasks_to_scale = [t for t in all_tasks if t["key"] not in existing_completed]
        scaled = ActionPlanService.scale_task_points(assessment, tasks_to_scale)
        points_earned = 0
        for task in scaled:
            if task["key"] == task_key:
                points_earned = task.get("points", 0)
                break

        CompletedTask.objects.get_or_create(
            user=request.user,
            assessment=assessment,
            task_key=task_key,
            defaults={"points_earned": points_earned}
        )

        old_score = assessment.readiness_score or 0
        new_score = min(old_score + points_earned, 100)
        assessment.readiness_score = new_score
        assessment.save(update_fields=["readiness_score"])

        return Response({"final_score": new_score}, status=status.HTTP_200_OK)


class DocumentsHomePageView(LoginRequiredMixin, TemplateView):
    template_name = "action_plan/documents.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["assessments"] = Assessment.objects.filter(user=self.request.user).order_by("-created_at")
        return context


class DocumentChecklistView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, assessment_id):
        if not require_premium(request.user):
            return Response({"detail": "Premium required"}, status=status.HTTP_403_FORBIDDEN)

        assessment = get_object_or_404(Assessment, id=assessment_id, user=request.user)
        data = ChecklistService.get_checklist_for_assessment(request.user, assessment)
        return Response(data)


class DeleteDocumentView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def delete(self, request, assessment_id, doc_type, object_id):
        if not require_premium(request.user):
            return Response({"detail": "Premium required"}, status=status.HTTP_403_FORBIDDEN)

        assessment = get_object_or_404(Assessment, id=assessment_id, user=request.user)
        task_key = None
        points_to_subtract = 0

        if doc_type in ["id_document", "payslip", "bank_statement"]:
            doc = get_object_or_404(UserDocument, id=object_id, user=request.user, assessment=assessment)
            task_key = f"upload_{doc.document_type}"
            doc.file.delete(save=False)
            doc.delete()
        elif doc_type == "reference_letter":
            ref = get_object_or_404(ReferenceLetter, id=object_id, user=request.user, assessment=assessment)
            task_key = "add_reference_letter"
            if ref.file:
                ref.file.delete(save=False)
            ref.delete()
        elif doc_type == "cover_letter":
            cover = get_object_or_404(CoverLetter, id=object_id, user=request.user, assessment=assessment)
            task_key = "improve_cover_letter"
            cover.delete()
        else:
            return Response({"detail": "Invalid document type"}, status=status.HTTP_400_BAD_REQUEST)

        if task_key:
            completed_task = CompletedTask.objects.filter(
                user=request.user,
                assessment=assessment,
                task_key=task_key
            ).first()
            if completed_task:
                points_to_subtract = completed_task.points_earned
                completed_task.delete()

        # Subtract the points that were earned from this task (if any)
        old_score = assessment.readiness_score or 0
        new_score = max(old_score - points_to_subtract, 0)
        assessment.readiness_score = new_score
        assessment.save(update_fields=["readiness_score"])

        return Response({"detail": "Deleted successfully", "final_score": new_score}, status=status.HTTP_200_OK)