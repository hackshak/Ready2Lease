from django.shortcuts import render, redirect
from assessments.models import Assessment
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .services import build_detailed_breakdown, normalize_income_to_annual
from django.utils import timezone
from assessments.gap_analysis import generate_gap_analysis
from action_plan.services import ActionPlanService


# ==========================================================
# HELPER
# ==========================================================

def require_premium(user):
    return getattr(user, "is_premium", False)


# ==========================================================
# TEMPLATE VIEWS (PREMIUM REQUIRED)
# ==========================================================

def dashboard_home(request):

    if not request.user.is_authenticated:
        return redirect("login")

    if not require_premium(request.user):
        return redirect("dashboard_home")

    return render(request, "dashboard/dashboard_home.html")


def detailed_analysis(request):

    if not request.user.is_authenticated:
        return redirect("login")

    if not require_premium(request.user):
        return redirect("dashboard_home")

    return render(request, "dashboard/detailed_analysis.html")


# ==========================================================
# DETAILED READINESS ANALYSIS (PREMIUM REQUIRED)
# ==========================================================

class DetailedReadinessAnalysisView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        if not require_premium(request.user):
            return Response(
                {"detail": "Premium required."},
                status=status.HTTP_403_FORBIDDEN
            )

        assessment_id = request.query_params.get("assessment_id")

        if assessment_id:
            try:
                assessment = Assessment.objects.get(
                    id=assessment_id,
                    user=request.user
                )
            except Assessment.DoesNotExist:
                return Response(
                    {"detail": "Assessment not found."},
                    status=status.HTTP_404_NOT_FOUND
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

        base_score = assessment.readiness_score or 0

        final_score = ActionPlanService.get_final_score_for_assessment(
            request.user,
            assessment
        )

        previous_assessment = (
            Assessment.objects
            .filter(user=request.user)
            .exclude(id=assessment.id)
            .order_by("-created_at")
            .first()
        )

        score_prev = (
            previous_assessment.readiness_score
            if previous_assessment else base_score
        )

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

        categories = build_detailed_breakdown(assessment)

        breakdown = [
            {"key": c["category"], "value": c["score"]}
            for c in categories
        ]

        approval_probability = min(95, max(25, final_score))
        competitiveness_percentile = min(95, max(10, int(final_score * 0.9)))

        risk_signals = [
            {
                "category": c["category"],
                "reason": c["explanation"]
            }
            for c in categories
            if c["risk_level"] == "High"
        ]

        gaps, recommendations = generate_gap_analysis(
            assessment,
            {c["category"]: c["score"] for c in categories}
        )

        next_best_action = None
        if recommendations:
            top = recommendations[0]
            next_best_action = {
                "title": top["category"].replace("_", " ").title(),
                "suggestion": top["suggestion"],
                "priority": top["priority"]
            }

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
                "created_at": item.created_at.date().isoformat(),
                "days_ago": (now - item.created_at).days,
            })

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

        return Response({
            "assessment_id": assessment.id,
            "score": final_score,
            "score_prev": score_prev,
            "approval_probability": approval_probability,
            "competitiveness_percentile": competitiveness_percentile,
            "risk_signals": risk_signals,
            "next_best_action": next_best_action,
            "last_assessment": assessment.created_at.isoformat(),
            "user_name": request.user.first_name or request.user.email,
            "postcode": assessment.postcode,
            "suburb": assessment.suburb,
            "income_weekly": income_weekly,
            "target_rent_weekly": target_rent_weekly,
            "avg_rent_weekly": avg_rent_weekly,
            "breakdown": breakdown,
            "gaps": gaps,
            "recommendations": recommendations,
            "steps": steps,
            "previous_assessments": previous_list,
            "risk_level": assessment.risk_level,
            "is_premium": True
        }, status=status.HTTP_200_OK)


# ==========================================================
# CATEGORY SCORES VIEW (NOW FULLY PREMIUM)
# ==========================================================

class CalculateCategoryScoresView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, assessment_id=None, format=None):

        if not require_premium(request.user):
            return Response(
                {"detail": "Premium required."},
                status=status.HTTP_403_FORBIDDEN
            )

        if assessment_id:
            try:
                assessment = Assessment.objects.get(
                    id=assessment_id,
                    user=request.user
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

        assessments = (
            Assessment.objects
            .filter(user=request.user)
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