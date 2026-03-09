from rest_framework import serializers
from .models import TenantReport


class TenantReportSerializer(serializers.ModelSerializer):

    assessment_name = serializers.CharField(
        source="assessment.full_name",
        read_only=True
    )

    assessment_date = serializers.DateTimeField(
        source="assessment.created_at",
        read_only=True
    )

    class Meta:
        model = TenantReport
        fields = [
            "id",
            "report_id",
            "score",
            "pdf_file",
            "created_at",
            "assessment_name",
            "assessment_date"
        ]