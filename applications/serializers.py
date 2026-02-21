from rest_framework import serializers
from .models import Application


class ApplicationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Application
        fields = [
            'id',
            'property_address',
            'company_name',
            'contact_person',
            'contact_email',
            'contact_phone',
            'rent_amount',
            'date_applied',
            'interview_date',
            'follow_up_date',
            'documents_submitted',
            'status',
            'notes',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']