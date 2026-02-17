from django.db import models

EMPLOYMENT_CHOICES = [
    ('full_time', 'Full time'),
    ('part_time', 'Part time'),
    ('self_employed', 'Self-employed'),
    ('student', 'Student'),
    ('retired', 'Retired'),
]

RENTAL_HISTORY_CHOICES = [
    ('rented_locally', 'Rented locally'),
    ('rented_overseas', 'Rented overseas'),
    ('first_time_renter', 'First-time renter'),
    ('owned_home', 'Owned previous home'),
]

PROOF_OF_INCOME_CHOICES = [
    ('recent_payslip', 'Recent payslip'),
    ('bank_statements', 'Bank statements only'),
    ('none', 'None'),
]

DOCUMENTS_CHOICES = [
    ('passport', 'Passport/Birth Cert'),
    ('driver_license', 'Driver license'),
    ('medicare', 'Medicare card'),
    ('bank_statement', 'Bank statement'),
    ('tenant_ledger', 'Tenant ledger'),
]

class Assessment(models.Model):
    session_key = models.CharField(max_length=100)
    full_name = models.CharField(max_length=255)
    postcode = models.CharField(max_length=10)
    suburb = models.CharField(max_length=255, blank=True)
    monthly_rent_budget = models.DecimalField(max_digits=10, decimal_places=2)


    postcode = models.CharField(max_length=20, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)

    lat = models.FloatField(blank=True, null=True)
    lon = models.FloatField(blank=True, null=True)


    employment_status = models.CharField(max_length=20, choices=EMPLOYMENT_CHOICES, blank=True)
    time_in_role = models.CharField(max_length=50, blank=True)
    rental_history = models.CharField(max_length=20, choices=RENTAL_HISTORY_CHOICES, blank=True)

    household_income = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    household_income_period = models.CharField(max_length=10, choices=[('annual','Annually'),('monthly','Monthly'),('weekly','Weekly')], blank=True)
    individual_income = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    individual_income_period = models.CharField(max_length=10, choices=[('annual','Annually'),('monthly','Monthly'),('weekly','Weekly')], blank=True)
    
    documents = models.JSONField(default=list, blank=True)
    proof_of_income = models.CharField(max_length=20, choices=PROOF_OF_INCOME_CHOICES, blank=True)

    moving_with_adults = models.PositiveIntegerField(null=True, blank=True)
    moving_with_children = models.PositiveIntegerField(null=True, blank=True)
    moving_with_pets = models.PositiveIntegerField(null=True, blank=True)
    context_issues = models.TextField(blank=True)

    readiness_score = models.IntegerField(null=True, blank=True)
    risk_level = models.CharField(max_length=20, blank=True)
    strengths = models.JSONField(default=list, blank=True)
    weaknesses = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Assessment ({self.full_name}) - {self.session_key}"
