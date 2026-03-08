from django.db.models import Sum
from assessments.models import Assessment
from dashboard.services import build_detailed_breakdown
from .models import CompletedTask


TASK_WEIGHTS = {
    "upload_payslip": 5,
    "upload_bank_statement": 2,
    "add_reference_letter": 3,
    "improve_cover_letter": 4,
    "improve_income_strength": 6,
    "improve_employment_stability": 5,
    "improve_rental_history": 5,
    "improve_competitiveness": 4,
}


class ActionPlanService:

    # ------------------------------------------------
    # Latest assessment
    # ------------------------------------------------
    @staticmethod
    def get_latest_assessment(user):

        return (
            Assessment.objects
            .filter(user=user)
            .order_by("-created_at")
            .first()
        )

    # ------------------------------------------------
    # ALL POSSIBLE TASKS (used for scoring)
    # ------------------------------------------------
    @staticmethod
    def get_all_possible_tasks(assessment):

        tasks = [
            {
                "key": "upload_payslip",
                "title": "Upload Payslip",
                "description": "Upload a recent payslip to strengthen income proof.",
                "weight": TASK_WEIGHTS["upload_payslip"],
                "type": "document",
                "document_type": "payslip"
            },
            {
                "key": "upload_bank_statement",
                "title": "Upload Bank Statement",
                "description": "Provide bank statement for financial credibility.",
                "weight": TASK_WEIGHTS["upload_bank_statement"],
                "type": "document",
                "document_type": "bank_statement"
            },
            {
                "key": "add_reference_letter",
                "title": "Upload Reference Letter",
                "description": "Upload a landlord or employer reference letter.",
                "weight": TASK_WEIGHTS["add_reference_letter"],
                "type": "reference"
            },
            {
                "key": "improve_cover_letter",
                "title": "Upload Cover Letter",
                "description": "Upload your rental cover letter as a PDF.",
                "weight": TASK_WEIGHTS["improve_cover_letter"],
                "type": "cover_letter"
            },
            {
                "key": "improve_income_strength",
                "title": "Improve Income Strength",
                "description": "Consider reducing rent target or adding a guarantor.",
                "weight": TASK_WEIGHTS["improve_income_strength"],
                "type": "strategic"
            },
            {
                "key": "improve_employment_stability",
                "title": "Strengthen Employment Stability",
                "description": "Provide employment contract or proof of stable income.",
                "weight": TASK_WEIGHTS["improve_employment_stability"],
                "type": "strategic"
            },
            {
                "key": "improve_rental_history",
                "title": "Improve Rental History Signal",
                "description": "Add strong references or rental background details.",
                "weight": TASK_WEIGHTS["improve_rental_history"],
                "type": "strategic"
            },
            {
                "key": "improve_competitiveness",
                "title": "Boost Overall Competitiveness",
                "description": "Focus on improving weakest scoring areas.",
                "weight": TASK_WEIGHTS["improve_competitiveness"],
                "type": "strategic"
            }
        ]

        return tasks

    # ------------------------------------------------
    # SCALE TASK POINTS TO FILL GAP
    # ------------------------------------------------
    @staticmethod
    def scale_task_points(assessment, tasks):

        if not tasks:
            return tasks

        base_score = assessment.readiness_score or 0
        missing_points = max(0, 100 - base_score)

        total_weight = sum(task["weight"] for task in tasks)

        scaled_tasks = []

        for task in tasks:

            weight = task["weight"]
            points = (weight / total_weight) * missing_points

            t = task.copy()
            t["points"] = round(points)

            scaled_tasks.append(t)

        return scaled_tasks

    # ------------------------------------------------
    # TASKS VISIBLE TO USER
    # ------------------------------------------------
    @staticmethod
    def generate_tasks_for_assessment(assessment):

        if not assessment:
            return []

        user = assessment.user

        completed = set(
            CompletedTask.objects
            .filter(user=user, assessment=assessment)
            .values_list("task_key", flat=True)
        )

        all_tasks = ActionPlanService.get_all_possible_tasks(assessment)

        scaled_tasks = ActionPlanService.scale_task_points(
            assessment,
            all_tasks
        )

        visible_tasks = []

        for task in scaled_tasks:

            if task["key"] in completed:
                continue

            if task["key"] == "upload_payslip" and \
               assessment.ap_documents.filter(document_type="payslip").exists():
                continue

            if task["key"] == "upload_bank_statement" and \
               assessment.ap_documents.filter(document_type="bank_statement").exists():
                continue

            if task["key"] == "add_reference_letter" and \
               assessment.ap_reference_letters.filter(file__isnull=False).exists():
                continue

            if task["key"] == "improve_cover_letter":
                cover = assessment.ap_cover_letters.first()
                if cover and cover.file:
                    continue

            visible_tasks.append(task)

        return visible_tasks

    # ------------------------------------------------
    # IMPROVEMENT SCORE
    # ------------------------------------------------
    @staticmethod
    def get_improvement_score_for_assessment(assessment):

        if not assessment:
            return 0

        user = assessment.user

        completed = set(
            CompletedTask.objects
            .filter(user=user, assessment=assessment)
            .values_list("task_key", flat=True)
        )

        all_tasks = ActionPlanService.get_all_possible_tasks(assessment)

        scaled_tasks = ActionPlanService.scale_task_points(
            assessment,
            all_tasks
        )

        improvement = 0

        for task in scaled_tasks:
            if task["key"] in completed:
                improvement += task["points"]

        return improvement

    # ------------------------------------------------
    # FINAL SCORE
    # ------------------------------------------------
    @staticmethod
    def get_final_score_for_assessment(user, assessment):

        if not assessment:
            return 0

        if assessment.user != user:
            return 0

        base_score = assessment.readiness_score or 0

        if not getattr(user, "is_premium", False):
            return base_score

        improvement = ActionPlanService.get_improvement_score_for_assessment(
            assessment
        )

        return min(base_score + improvement, 100)