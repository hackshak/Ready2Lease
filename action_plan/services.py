from assessments.models import Assessment
from .models import CompletedTask, UserDocument, ReferenceLetter, CoverLetter


TASK_POINTS = {
    "upload_payslip": 5,
    "upload_bank_statement": 2,
    "add_reference_letter": 3,
    "improve_cover_letter": 4,
}


class ActionPlanService:

    @staticmethod
    def get_latest_assessment(user):
        return (
            Assessment.objects
            .filter(user=user)
            .order_by("-created_at")
            .first()
        )

    @staticmethod
    def get_completed_keys(user):
        return set(
            user.ap_completed_tasks.values_list("task_key", flat=True)
        )

    @staticmethod
    def generate_tasks(user):
        assessment = ActionPlanService.get_latest_assessment(user)
        if not assessment:
            return []

        completed = ActionPlanService.get_completed_keys(user)
        tasks = []

        # Payslip
        if not UserDocument.objects.filter(
            user=user,
            document_type="payslip"
        ).exists() and "upload_payslip" not in completed:

            tasks.append({
                "key": "upload_payslip",
                "title": "Upload Payslip",
                "description": "Upload a recent payslip to strengthen income proof.",
                "points": TASK_POINTS["upload_payslip"],
                "type": "document",
                "document_type": "payslip"
            })

        # Bank Statement
        if not UserDocument.objects.filter(
            user=user,
            document_type="bank_statement"
        ).exists() and "upload_bank_statement" not in completed:

            tasks.append({
                "key": "upload_bank_statement",
                "title": "Upload Bank Statement",
                "description": "Provide bank statement for financial credibility.",
                "points": TASK_POINTS["upload_bank_statement"],
                "type": "document",
                "document_type": "bank_statement"
            })

        # Reference Letter
        if not ReferenceLetter.objects.filter(user=user).exists() \
                and "add_reference_letter" not in completed:

            tasks.append({
                "key": "add_reference_letter",
                "title": "Add Reference Letter",
                "description": "Upload or write a landlord/employer reference.",
                "points": TASK_POINTS["add_reference_letter"],
                "type": "reference"
            })

        # Cover Letter
        cover = getattr(user, "ap_cover_letter", None)
        if (not cover or len(cover.content.strip()) < 200) \
                and "improve_cover_letter" not in completed:

            tasks.append({
                "key": "improve_cover_letter",
                "title": "Improve Cover Letter",
                "description": "Write a compelling rental cover letter (min 200 chars).",
                "points": TASK_POINTS["improve_cover_letter"],
                "type": "cover_letter"
            })

        return tasks

    @staticmethod
    def get_improvement_score(user):
        return sum(
            user.ap_completed_tasks.values_list("points_awarded", flat=True)
        )

    @staticmethod
    def get_final_score(user):
        assessment = ActionPlanService.get_latest_assessment(user)
        if not assessment:
            return 0

        # Base readiness score (from assessment engine)
        base_score = assessment.readiness_score or 0

        # Improvement points (completed action plan tasks)
        improvement_score = ActionPlanService.get_improvement_score(user)

        # Final score = base + improvements
        final_score = base_score + improvement_score

        # Clamp to 100 (important)
        final_score = min(final_score, 100)

        return final_score
