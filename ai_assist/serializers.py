from rest_framework import serializers
from .models import AIAssistMessage


class AIAssistMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIAssistMessage
        fields = ["id", "role", "content", "created_at"]