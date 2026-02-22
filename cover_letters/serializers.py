from rest_framework import serializers
from .models import CoverLetter


class CoverLetterCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoverLetter
        fields = [
            "property_address",
            "tone",
            "employment_type",
            "rental_history_type",
            "base_inputs",
        ]


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