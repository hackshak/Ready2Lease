from django.db import models
from django.conf import settings
from assessments.models import Assessment


class UserDocument(models.Model):
    DOCUMENT_TYPES = [
        ("payslip", "Payslip"),
        ("bank_statement", "Bank Statement"),
        ("id_document", "ID Document"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ap_documents"
    )
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    file = models.FileField(upload_to="action_plan/documents/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.document_type}"


class ReferenceLetter(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ap_reference_letters"
    )
    text_content = models.TextField(blank=True)
    file = models.FileField(
        upload_to="action_plan/reference_letters/",
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)


class CoverLetter(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ap_cover_letter"
    )
    content = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)


class CompletedTask(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ap_completed_tasks"
    )
    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name="completed_tasks"
    )
    task_key = models.CharField(max_length=100)
    points_awarded = models.IntegerField()
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("assessment", "task_key")
