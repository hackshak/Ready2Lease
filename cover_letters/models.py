from django.conf import settings
from django.db import models
from django.utils import timezone


class CoverLetter(models.Model):

    # =========================
    # STATUS
    # =========================
    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("generated", "Generated"),
        ("finalized", "Finalized"),
    )

    # =========================
    # TONE
    # =========================
    TONE_CHOICES = (
        ("professional", "Professional"),
        ("friendly", "Friendly"),
        ("confident", "Confident"),
        ("direct", "Short & Direct"),
    )

    # =========================
    # EMPLOYMENT TYPE
    # =========================
    EMPLOYMENT_TYPE_CHOICES = (
        ("full_time", "Full Time"),
        ("part_time", "Part Time"),
        ("student", "Student"),
        ("retired", "Retired"),
    )

    # =========================
    # RENTAL HISTORY TYPE
    # =========================
    RENTAL_HISTORY_TYPE_CHOICES = (
        ("first_time", "First Time Renter"),
        ("rented_before", "Rented Before"),
        ("rented_overseas", "Rented Overseas"),
    )

    # =========================
    # RELATIONS
    # =========================
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cover_letters"
    )

    # =========================
    # PROPERTY
    # =========================
    property_address = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    # =========================
    # STRUCTURED FIELDS
    # =========================
    tone = models.CharField(
        max_length=50,
        choices=TONE_CHOICES,
        default="professional"
    )

    employment_type = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_TYPE_CHOICES,
        blank=True,
        null=True
    )

    rental_history_type = models.CharField(
        max_length=20,
        choices=RENTAL_HISTORY_TYPE_CHOICES,
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft"
    )

    # =========================
    # FLEXIBLE INPUT DATA
    # =========================
    base_inputs = models.JSONField(default=dict)

    # =========================
    # CONTENT
    # =========================
    generated_content = models.TextField(blank=True, null=True)
    edited_content = models.TextField(blank=True, null=True)

    # =========================
    # AI SCORING
    # =========================
    score = models.PositiveIntegerField(blank=True, null=True)
    ai_feedback = models.JSONField(blank=True, null=True)

    is_premium_generated = models.BooleanField(default=False)

    # =========================
    # TIMESTAMPS
    # =========================
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} - CoverLetter #{self.id}"

    @property
    def final_content(self):
        return self.edited_content or self.generated_content