from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

from assessments.models import Assessment
from .services import ActionPlanService, TASK_POINTS
from .models import CompletedTask, UserDocument, ReferenceLetter, CoverLetter


# ==========================================================
# PAGE VIEW
# ==========================================================

class ActionPlanPageView(LoginRequiredMixin, TemplateView):
    template_name = "action_plan/action_plan.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_premium:
            return redirect("dashboard_home")
        return super().dispatch(request, *args, **kwargs)


# ==========================================================
# TASKS VIEW (NOW SUPPORTS ASSESSMENT SELECTION)
# URL: /tasks/<assessment_id>/
# ==========================================================

class ActionPlanTasksView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, assessment_id=None):

        if not request.user.is_premium:
            return Response({"detail": "Premium required"}, status=403)

        # If assessment_id not provided → fallback to latest
        if assessment_id:
            assessment = get_object_or_404(
                Assessment,
                id=assessment_id,
                user=request.user
            )
        else:
            assessment = ActionPlanService.get_latest_assessment(request.user)

        if not assessment:
            return Response({
                "tasks": [],
                "base_score": 0,
                "improvement_score": 0,
                "final_score": 0
            })

        tasks = ActionPlanService.generate_tasks_for_assessment(
            request.user,
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
        })


# ==========================================================
# UPLOAD DOCUMENT (NOW SUPPORTS ASSESSMENT)
# ==========================================================

class UploadDocumentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        assessment_id = request.data.get("assessment_id")
        doc_type = request.data.get("document_type")
        file = request.FILES.get("file")

        if not file:
            return Response({"detail": "File required"}, status=400)

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

        task_key = f"upload_{doc_type}"

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
        })


# ==========================================================
# ADD REFERENCE (NOW SUPPORTS ASSESSMENT)
# ==========================================================

class AddReferenceView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        assessment_id = request.data.get("assessment_id")
        text = request.data.get("text_content", "")
        file = request.FILES.get("file")

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

        CompletedTask.objects.get_or_create(
            user=request.user,
            assessment=assessment,
            task_key="add_reference_letter",
            defaults={"points_awarded": TASK_POINTS["add_reference_letter"]}
        )

        return Response({
            "final_score": ActionPlanService.get_final_score_for_assessment(
                request.user,
                assessment
            )
        })


# ==========================================================
# SAVE COVER LETTER (NOW SUPPORTS ASSESSMENT)
# ==========================================================

class SaveCoverLetterView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        assessment_id = request.data.get("assessment_id")
        content = request.data.get("content", "")

        if len(content.strip()) < 200:
            return Response(
                {"detail": "Minimum 200 characters required"},
                status=400
            )

        assessment = get_object_or_404(
            Assessment,
            id=assessment_id,
            user=request.user
        )

        CoverLetter.objects.update_or_create(
            user=request.user,
            assessment=assessment,
            defaults={"content": content}
        )

        CompletedTask.objects.get_or_create(
            user=request.user,
            assessment=assessment,
            task_key="improve_cover_letter",
            defaults={"points_awarded": TASK_POINTS["improve_cover_letter"]}
        )

        return Response({
            "final_score": ActionPlanService.get_final_score_for_assessment(
                request.user,
                assessment
            )
        })