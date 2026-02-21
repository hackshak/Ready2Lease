from django.db import models
from django.conf import settings


class Application(models.Model):

    STATUS_CHOICES = [
        ('Applied', 'Applied'),
        ('Interview', 'Interview'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    property_address = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255, blank=True, null=True)

    contact_person = models.CharField(max_length=150, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)

    rent_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    date_applied = models.DateField()
    interview_date = models.DateField(blank=True, null=True)
    follow_up_date = models.DateField(blank=True, null=True)

    documents_submitted = models.BooleanField(default=False)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Applied')

    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.property_address} - {self.status}"