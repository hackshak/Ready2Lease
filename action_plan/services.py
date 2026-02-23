# action_plan/services.py

from django.db.models import Sum
from assessments.models import Assessment
from dashboard.services import build_detailed_breakdown
from .models import CompletedTask


TASK_POINTS = {
    "upload_payslip": 5,
    "upload_bank_statement": 2,
    "add_reference_letter": 3,
    "improve_cover_letter": 4,

    # 🔥 NEW INTELLIGENCE TASKS
    "improve_income_strength": 6,
    "improve_employment_stability": 5,
    "improve_rental_history": 5,
    "improve_competitiveness": 4,
}


class ActionPlanService:

    # ------------------------------------------------
    # Get Latest Assessment
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
    # Generate Tasks (DOCUMENT + INTELLIGENT)
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

        tasks = []

        # =====================================================
        # 1️⃣ DOCUMENT TASKS (UNCHANGED)
        # =====================================================

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

        if (
            not assessment.ap_reference_letters.filter(
                file__isnull=False
            ).exists()
            and "add_reference_letter" not in completed
        ):
            tasks.append({
                "key": "add_reference_letter",
                "title": "Upload Reference Letter",
                "description": "Upload a landlord or employer reference letter.",
                "points": TASK_POINTS["add_reference_letter"],
                "type": "reference"
            })

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

        # =====================================================
        # 2️⃣ INTELLIGENT CATEGORY TASKS (NEW)
        # =====================================================

        categories = build_detailed_breakdown(assessment)
        scores = {c["category"]: c["score"] for c in categories}

        # Income Strength
        if (
            scores.get("income_strength", 100) < 50
            and "improve_income_strength" not in completed
        ):
            tasks.append({
                "key": "improve_income_strength",
                "title": "Improve Income Strength",
                "description": "Consider reducing rent target or adding a guarantor to improve affordability.",
                "points": TASK_POINTS["improve_income_strength"],
                "type": "strategic"
            })

        # Employment Stability
        if (
            scores.get("employment_stability", 100) < 60
            and "improve_employment_stability" not in completed
        ):
            tasks.append({
                "key": "improve_employment_stability",
                "title": "Strengthen Employment Stability",
                "description": "Provide employment contract or additional proof of stable income.",
                "points": TASK_POINTS["improve_employment_stability"],
                "type": "strategic"
            })

        # Rental History
        if (
            scores.get("rental_history", 100) < 60
            and "improve_rental_history" not in completed
        ):
            tasks.append({
                "key": "improve_rental_history",
                "title": "Improve Rental History Signal",
                "description": "Add strong references or additional rental background details.",
                "points": TASK_POINTS["improve_rental_history"],
                "type": "strategic"
            })

        # Overall Competitiveness
        if (
            scores.get("overall_competitiveness", 100) < 50
            and "improve_competitiveness" not in completed
        ):
            tasks.append({
                "key": "improve_competitiveness",
                "title": "Boost Overall Competitiveness",
                "description": "Focus on improving weakest scoring areas before applying widely.",
                "points": TASK_POINTS["improve_competitiveness"],
                "type": "strategic"
            })

        return tasks

    # ------------------------------------------------
    # Improvement Score
    # ------------------------------------------------
    @staticmethod
    def get_improvement_score_for_assessment(assessment):

        if not assessment:
            return 0

        result = (
            CompletedTask.objects
            .filter(user=assessment.user, assessment=assessment)
            .aggregate(total=Sum("points_awarded"))
        )

        return result["total"] or 0

    # ------------------------------------------------
    # Final Score (UNCHANGED LOGIC)
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

        improvement_score = (
            ActionPlanService.get_improvement_score_for_assessment(
                assessment
            )
        )

        return min(base_score + improvement_score, 100)