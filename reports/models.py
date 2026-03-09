import uuid
from django.db import models
from assessments.models import Assessment


class TenantReport(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name="reports"
    )

    report_id = models.CharField(max_length=100, unique=True)

    score = models.IntegerField()

    strengths = models.JSONField(default=list)
    risks = models.JSONField(default=list)
    actions = models.JSONField(default=list)

    pdf_file = models.FileField(upload_to="reports/tenant_reports/", null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report {self.report_id}"