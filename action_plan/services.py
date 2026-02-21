# action_plan/services.py

from assessments.models import Assessment
from .models import CompletedTask

TASK_POINTS = {
    "upload_payslip": 5,
    "upload_bank_statement": 2,
    "add_reference_letter": 3,
    "improve_cover_letter": 4,
}


class ActionPlanService:

    # ------------------------------------------------
    # Get Latest Assessment (used in fallback URL)
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
    # Generate Tasks (STRICTLY PER ASSESSMENT)
    # ------------------------------------------------
    @staticmethod
    def generate_tasks_for_assessment(assessment):

        if not assessment:
            return []

        completed = set(
            assessment.completed_tasks.values_list("task_key", flat=True)
        )

        tasks = []

        # ------------------------------------------------
        # Payslip
        # ------------------------------------------------
        if (
            not assessment.ap_documents.filter(
                document_type="payslip"
            ).exists()
            and "upload_payslip" not in completed
        ):
            tasks.append({
                "key": "upload_payslip",
                "title": "Upload Payslip",
                "description": "Upload a recent payslip to strengthen income proof.",
                "points": TASK_POINTS["upload_payslip"],
                "type": "document",
                "document_type": "payslip"
            })

        # ------------------------------------------------
        # Bank Statement
        # ------------------------------------------------
        if (
            not assessment.ap_documents.filter(
                document_type="bank_statement"
            ).exists()
            and "upload_bank_statement" not in completed
        ):
            tasks.append({
                "key": "upload_bank_statement",
                "title": "Upload Bank Statement",
                "description": "Provide bank statement for financial credibility.",
                "points": TASK_POINTS["upload_bank_statement"],
                "type": "document",
                "document_type": "bank_statement"
            })

        # ------------------------------------------------
        # Reference Letter
        # ------------------------------------------------
        if (
            not assessment.ap_reference_letters.filter(file__isnull=False).exists()
            and "add_reference_letter" not in completed
        ):
            tasks.append({
                "key": "add_reference_letter",
                "title": "Upload Reference Letter",
                "description": "Upload a landlord or employer reference letter.",
                "points": TASK_POINTS["add_reference_letter"],
                "type": "reference"
            })

        # ------------------------------------------------
        # Cover Letter (FILE BASED - UPDATED)
        # ------------------------------------------------
        cover = assessment.ap_cover_letters.first()

        if (
            (not cover or not cover.file)
            and "improve_cover_letter" not in completed
        ):
            tasks.append({
                "key": "improve_cover_letter",
                "title": "Upload Cover Letter",
                "description": "Upload your rental cover letter as a PDF.",
                "points": TASK_POINTS["improve_cover_letter"],
                "type": "cover_letter"
            })

        return tasks

    # ------------------------------------------------
    # Improvement Score Per Assessment
    # ------------------------------------------------
    @staticmethod
    def get_improvement_score_for_assessment(assessment):

        if not assessment:
            return 0

        return sum(
            assessment.completed_tasks.values_list(
                "points_awarded",
                flat=True
            )
        )

    # ------------------------------------------------
    # Final Score Per Assessment
    # ------------------------------------------------
    @staticmethod
    def get_final_score_for_assessment(user, assessment):

        if not assessment:
            return 0

        base_score = assessment.readiness_score or 0

        if not getattr(user, "is_premium", False):
            return base_score

        improvement_score = (
            ActionPlanService.get_improvement_score_for_assessment(
                assessment
            )
        )

        return min(base_score + improvement_score, 100)