from assessments.models import Assessment
from .models import CompletedTask


TASK_WEIGHTS = {
    "upload_payslip": 5,
    "upload_bank_statement": 4,
    "add_reference_letter": 4,
    "improve_cover_letter": 4,
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
    # All document tasks
    # ------------------------------------------------
    @staticmethod
    def get_all_possible_tasks(assessment):

        return [
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
                "description": "Provide a bank statement to improve financial credibility.",
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
                "description": "Upload your rental cover letter.",
                "weight": TASK_WEIGHTS["improve_cover_letter"],
                "type": "cover_letter"
            },
        ]

    # ------------------------------------------------
    # Scale tasks to fill score gap
    # ------------------------------------------------
    @staticmethod
    def scale_task_points(assessment, tasks):

        base_score = assessment.readiness_score or 0
        missing_points = max(0, 100 - base_score)

        if not tasks or missing_points == 0:
            return tasks

        total_weight = sum(t["weight"] for t in tasks)

        scaled = []
        assigned = 0

        for i, task in enumerate(tasks):

            t = task.copy()

            if i == len(tasks) - 1:
                points = missing_points - assigned
            else:
                points = int((task["weight"] / total_weight) * missing_points)

            assigned += points
            t["points"] = points

            scaled.append(t)

        return scaled

    # ------------------------------------------------
    # Visible tasks (not yet completed)
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

        tasks = ActionPlanService.get_all_possible_tasks(assessment)

        tasks = ActionPlanService.scale_task_points(
            assessment,
            tasks
        )

        visible = []

        for task in tasks:

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

            visible.append(task)

        return visible

    # ------------------------------------------------
    # Improvement score
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

        tasks = ActionPlanService.get_all_possible_tasks(assessment)

        tasks = ActionPlanService.scale_task_points(
            assessment,
            tasks
        )

        improvement = 0

        for task in tasks:
            if task["key"] in completed:
                improvement += task["points"]

        return improvement

    # ------------------------------------------------
    # Final score
    # ------------------------------------------------
    @staticmethod
    def get_final_score_for_assessment(user, assessment):

        if not assessment:
            return 0

        base_score = assessment.readiness_score or 0

        if not getattr(user, "is_premium", False):
            return base_score

        improvement = ActionPlanService.get_improvement_score_for_assessment(
            assessment
        )

        return min(base_score + improvement, 100)