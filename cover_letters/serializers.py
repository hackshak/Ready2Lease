from rest_framework import serializers
from .models import CoverLetter


class CoverLetterCreateSerializer(serializers.Serializer):  # NOT ModelSerializer
    property_address = serializers.CharField(required=False, allow_blank=True)
    tone = serializers.ChoiceField(choices=["professional", "friendly", "confident", "direct"])
    employment_type = serializers.ChoiceField(
        choices=["full_time", "part_time", "student", "retired"], required=False
    )
    rental_history_type = serializers.ChoiceField(
        choices=["first_time", "rented_before", "rented_overseas"], required=False
    )
    base_inputs = serializers.DictField()


class CoverLetterDetailSerializer(serializers.ModelSerializer):
    content = serializers.SerializerMethodField()

    class Meta:
        model = CoverLetter
        fields = [
            "id",
            "property_address",
            "tone",
            "employment_type",
            "rental_history_type",
            "content",
            "score",
            "ai_feedback",
            "created_at",
        ]

    def get_content(self, obj):
        return obj.final_content


class CoverLetterUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoverLetter
        fields = ["edited_content"]