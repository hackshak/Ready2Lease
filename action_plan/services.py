from assessments.models import Assessment
from .models import CompletedTask
from django.db.models import Sum

TASK_WEIGHTS = {
    "upload_payslip": 5,
    "upload_bank_statement": 4,
    "add_reference_letter": 4,
    "improve_cover_letter": 4,
}


class ActionPlanService:

    @staticmethod
    def get_latest_assessment(user):
        return Assessment.objects.filter(user=user).order_by("-created_at").first()

    @staticmethod
    def get_all_possible_tasks(assessment):
        return [
            {
                "key": "upload_payslip",
                "title": "Upload Payslip",
                "description": "Upload a recent payslip to strengthen income proof.",
                "weight": TASK_WEIGHTS["upload_payslip"],
                "type": "document",
                "document_type": "payslip",
            },
            {
                "key": "upload_bank_statement",
                "title": "Upload Bank Statement",
                "description": "Provide a bank statement to improve financial credibility.",
                "weight": TASK_WEIGHTS["upload_bank_statement"],
                "type": "document",
                "document_type": "bank_statement",
            },
            {
                "key": "add_reference_letter",
                "title": "Upload Reference Letter",
                "description": "Upload a landlord or employer reference letter.",
                "weight": TASK_WEIGHTS["add_reference_letter"],
                "type": "reference",
            },
            {
                "key": "improve_cover_letter",
                "title": "Upload Cover Letter",
                "description": "Upload your rental cover letter.",
                "weight": TASK_WEIGHTS["improve_cover_letter"],
                "type": "cover_letter",
            },
        ]

    @staticmethod
    def scale_task_points(assessment, tasks):
        """Return tasks with 'points' field based on current gap to 100."""
        if not tasks:
            return []

        current_score = assessment.readiness_score or 0
        missing_points = max(0, 100 - current_score)

        total_weight = sum(t.get("weight", 0) for t in tasks)
        if missing_points == 0 or total_weight == 0:
            for task in tasks:
                task["points"] = 0
            return tasks

        scaled = []
        assigned = 0

        for i, task in enumerate(tasks):
            t = task.copy()
            if i == len(tasks) - 1:
                points = missing_points - assigned
            else:
                points = int((task["weight"] / total_weight) * missing_points)
            assigned += points
            t["points"] = max(points, 0)
            scaled.append(t)

        return scaled

    @staticmethod
    def generate_tasks_for_assessment(assessment):
        if not assessment:
            return []

        user = assessment.user
        completed_keys = set(
            CompletedTask.objects.filter(user=user, assessment=assessment)
            .values_list("task_key", flat=True)
        )

        all_tasks = ActionPlanService.get_all_possible_tasks(assessment)

        visible_tasks = []
        for task in all_tasks:
            if task["key"] in completed_keys:
                continue
            if task["key"] == "upload_payslip" and assessment.ap_documents.filter(document_type="payslip").exists():
                continue
            if task["key"] == "upload_bank_statement" and assessment.ap_documents.filter(document_type="bank_statement").exists():
                continue
            if task["key"] == "add_reference_letter" and assessment.ap_reference_letters.filter(file__isnull=False).exists():
                continue
            if task["key"] == "improve_cover_letter":
                cover = assessment.ap_cover_letters.first()
                if cover and cover.file:
                    continue
            visible_tasks.append(task)

        return ActionPlanService.scale_task_points(assessment, visible_tasks)

    @staticmethod
    def get_improvement_score_for_assessment(assessment):
        # Not used for final score anymore, but kept for possible other uses
        return CompletedTask.objects.filter(
            assessment=assessment,
            user=assessment.user
        ).aggregate(total=Sum("points_earned"))["total"] or 0

    @staticmethod
    def get_final_score_for_assessment(user, assessment):
        """Final score is stored directly in assessment.readiness_score."""
        if not assessment:
            return 0
        # Free users see only base score (without improvements)
        if not getattr(user, "is_premium", False):
            pass
        return min(assessment.readiness_score or 0, 100)