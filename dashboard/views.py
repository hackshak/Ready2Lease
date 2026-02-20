from django.shortcuts import render
from assessments.models import Assessment,DOCUMENTS_CHOICES
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .services import build_detailed_breakdown,normalize_income_to_annual
from django.utils import timezone
from assessments.gap_analysis import generate_gap_analysis
from action_plan.services import ActionPlanService



# Create your views here.
def dashboard_home(request):
    return render(request,"dashboard/dashboard_home.html")





# Detailed Analysis page
def detailed_analysis(request):
    return render(request,"dashboard/detailed_analysis.html")





class DetailedReadinessAnalysisView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, assessment_id=None):

        # 🔒 Premium gate
        if not getattr(request.user, "is_premium", False):
            return Response(
                {"detail": "Premium required."},
                status=status.HTTP_403_FORBIDDEN
            )

        # -----------------------------
        # Get latest assessment
        # -----------------------------
        if assessment_id:
            assessment = Assessment.objects.get(
                id=assessment_id,
                user=request.user
            )
        else:
            assessment = (
                Assessment.objects
                .filter(user=request.user)
                .order_by("-created_at")
                .first()
            )

        if not assessment:
            return Response(
                {"detail": "No assessment found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # -----------------------------
        # 🔥 NEW: Use Final Score (Base + Improvements)
        # -----------------------------
        # 🔥 Use selected assessment base score
        base_score = assessment.readiness_score or 0

        # Apply improvements on THIS assessment only
        final_score = ActionPlanService.get_final_score_for_assessment(
            request.user,
            assessment
        )

        # -----------------------------
        # Previous assessment (trend)
        # -----------------------------
        previous_assessment = (
            Assessment.objects
            .filter(user=request.user)
            .exclude(id=assessment.id)
            .order_by("-created_at")
            .first()
        )

        if previous_assessment:
            prev_base = previous_assessment.readiness_score or 0
        else:
            prev_base = base_score

        # Trend compares FINAL score now vs previous BASE
        score_prev = prev_base

        # -----------------------------
        # Financial metrics
        # -----------------------------
        annual_income = normalize_income_to_annual(
            assessment.household_income or assessment.individual_income,
            assessment.household_income_period or assessment.individual_income_period
        )

        income_weekly = round((annual_income / 52), 2) if annual_income else 0
        target_rent_weekly = round((float(assessment.monthly_rent_budget or 0) / 4), 2)

        suburb_median_rent = {
            'Sydney CBD': 3000,
            'Darling Harbour': 3200,
            'The Rocks': 3100,
            'Melbourne CBD': 2500,
            'Docklands': 2400,
            'Southbank': 2600,
            'Brisbane CBD': 2000,
            'Fortitude Valley': 2100,
        }

        avg_rent_monthly = suburb_median_rent.get(assessment.suburb or "", 2500)
        avg_rent_weekly = round(avg_rent_monthly / 4, 2)

        # -----------------------------
        # Category breakdown
        # -----------------------------
        categories = build_detailed_breakdown(assessment)

        category_scores = {
            c["category"]: c["score"]
            for c in categories
        }

        risk_level = assessment.risk_level

        breakdown = [
            {
                "key": c["category"],
                "value": c["score"]
            }
            for c in categories
        ]

        # -----------------------------
        # GAP ANALYSIS
        # -----------------------------
        gaps, recommendations = generate_gap_analysis(
            assessment,
            category_scores
        )

        priority_order = {"high": 1, "medium": 2, "low": 3, "boost": 4}
        recommendations = sorted(
            recommendations,
            key=lambda x: priority_order.get(x.get("priority"), 5)
        )

        assessment.gap_analysis = gaps
        assessment.recommendations = recommendations
        assessment.save(update_fields=["gap_analysis", "recommendations"])

        # -----------------------------
        # Previous assessments list
        # -----------------------------
        now = timezone.now()

        previous_list = []
        for item in Assessment.objects.filter(user=request.user).order_by("-created_at"):
            score_value = ActionPlanService.get_final_score_for_assessment(
                request.user,
                item
            )

            previous_list.append({
                "id": item.id,
                "score": score_value,
                "risk_level": item.risk_level,
                "days_ago": (now - item.created_at).days,
                "created_at": item.created_at.date().isoformat(),
            })

        # -----------------------------
        # Dynamic Improvement Steps
        # -----------------------------
        steps = [
            {
                "icon": "⚠️" if r["priority"] == "high" else "📌",
                "title": r["category"].replace("_", " ").title(),
                "desc": r["suggestion"],
                "impact": 8 if r["priority"] == "high" else 5,
                "actionLabel": "Fix Now"
            }
            for r in recommendations[:3]
        ]

        # -----------------------------
        # Activity
        # -----------------------------
        activity = [
            {
                "icon": "🧾",
                "title": "Assessment completed",
                "desc": "Your readiness score and gap analysis were calculated.",
                "when": "Recently"
            }
        ]

        # -----------------------------
        # Final Response
        # -----------------------------
        return Response({
            "assessment_id": assessment.id,
            "score": final_score,  # 🔥 ALWAYS FINAL SCORE
            "score_prev": score_prev,
            "risk_level": risk_level,
            "last_assessment": assessment.created_at.isoformat(),

            "user_name": request.user.first_name or request.user.email,
            "postcode": assessment.postcode,
            "suburb": assessment.suburb,

            "income_weekly": income_weekly,
            "target_rent_weekly": target_rent_weekly,
            "avg_rent_weekly": avg_rent_weekly,

            "breakdown": breakdown,
            "categories": categories,

            "gaps": gaps,
            "recommendations": recommendations,

            "previous_assessments": previous_list,
            "steps": steps,
            "activity": activity,

            "is_premium": True
        }, status=status.HTTP_200_OK)






class CalculateCategoryScoresView(APIView):
    """
    - If assessment_id provided → return detailed category breakdown (Premium only)
    - Otherwise → list user/session assessments
    """

    def get(self, request, assessment_id=None, format=None):

        user = request.user if request.user.is_authenticated else None
        session_key = request.session.session_key

        # ======================================================
        # DETAILED BREAKDOWN (Premium Only)
        # ======================================================
        if assessment_id:

            if not user:
                return Response(
                    {"detail": "Login required."},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            if not user.is_premium:
                return Response(
                    {"detail": "Premium required."},
                    status=status.HTTP_403_FORBIDDEN
                )

            try:
                assessment = Assessment.objects.get(
                    id=assessment_id,
                    user=user
                )
            except Assessment.DoesNotExist:
                return Response(
                    {"detail": "Assessment not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            categories = build_detailed_breakdown(assessment)

            return Response({
                "assessment_id": assessment.id,
                "created_at": assessment.created_at.isoformat(),
                "categories": categories,
                "readiness_score": assessment.readiness_score,
                "risk_level": assessment.risk_level
            }, status=status.HTTP_200_OK)

        # ======================================================
        # LIST ALL ASSESSMENTS (User or Session)
        # ======================================================
        if user:
            assessments = (
                Assessment.objects
                .filter(user=user)
                .order_by('-created_at')
            )
        else:
            assessments = (
                Assessment.objects
                .filter(session_key=session_key)
                .order_by('-created_at')
            )

        data = [
            {
                "id": a.id,
                "full_name": a.full_name or "Anonymous",
                "created_at": a.created_at.isoformat(),
                "monthly_rent_budget": float(a.monthly_rent_budget or 0),
                "postcode": a.postcode,
                "score": a.readiness_score or 0,
                "risk_level": a.risk_level,
            }
            for a in assessments
        ]

        return Response({
            "assessments": data,
            "count": len(data)
        }, status=status.HTTP_200_OK)