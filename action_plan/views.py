from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import transaction
from .services import ActionPlanService, TASK_POINTS
from .models import CompletedTask, UserDocument, ReferenceLetter, CoverLetter
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin



class ActionPlanPageView(LoginRequiredMixin, TemplateView):
    template_name = "action_plan/action_plan.html"

    def dispatch(self, request, *args, **kwargs):
        # Premium Gate
        if not request.user.is_premium:
            from django.shortcuts import redirect
            return redirect("dashboard_home") 
        return super().dispatch(request, *args, **kwargs)



class ActionPlanTasksView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        if not request.user.is_premium:
            return Response({"detail": "Premium required"}, status=403)

        tasks = ActionPlanService.generate_tasks(request.user)
        assessment = ActionPlanService.get_latest_assessment(request.user)

        return Response({
            "tasks": tasks,
            "base_score": assessment.readiness_score if assessment else 0,
            "improvement_score": ActionPlanService.get_improvement_score(request.user),
            "final_score": ActionPlanService.get_final_score(request.user),
        })

class UploadDocumentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        doc_type = request.data.get("document_type")
        file = request.FILES.get("file")

        if not file:
            return Response({"detail": "File required"}, status=400)

        UserDocument.objects.create(
            user=request.user,
            document_type=doc_type,
            file=file
        )

        # Complete task if exists
        task_key = f"upload_{doc_type}"
        if task_key in TASK_POINTS:
            CompletedTask.objects.get_or_create(
                user=request.user,
                task_key=task_key,
                defaults={"points_awarded": TASK_POINTS[task_key]}
            )

        return Response({
            "final_score": ActionPlanService.get_final_score(request.user)
        })


class AddReferenceView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        text = request.data.get("text_content", "")
        file = request.FILES.get("file")

        ReferenceLetter.objects.create(
            user=request.user,
            text_content=text,
            file=file
        )

        CompletedTask.objects.get_or_create(
            user=request.user,
            task_key="add_reference_letter",
            defaults={"points_awarded": TASK_POINTS["add_reference_letter"]}
        )

        return Response({
            "final_score": ActionPlanService.get_final_score(request.user)
        })


class SaveCoverLetterView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        content = request.data.get("content", "")

        if len(content.strip()) < 200:
            return Response(
                {"detail": "Minimum 200 characters required"},
                status=400
            )

        CoverLetter.objects.update_or_create(
            user=request.user,
            defaults={"content": content}
        )

        CompletedTask.objects.get_or_create(
            user=request.user,
            task_key="improve_cover_letter",
            defaults={"points_awarded": TASK_POINTS["improve_cover_letter"]}
        )

        return Response({
            "final_score": ActionPlanService.get_final_score(request.user)
        })
