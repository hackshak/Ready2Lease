import re
import requests
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.http import JsonResponse
from django.views.generic import TemplateView
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Assessment
from .serializers import AssessmentSerializer
from .gap_analysis import generate_gap_analysis


class AssessmentListAPIView(ListAPIView):
    serializer_class = AssessmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Assessment.objects.filter(user=self.request.user).order_by("-created_at")


class AssessmentDetailAPIView(RetrieveAPIView):
    queryset = Assessment.objects.all()
    serializer_class = AssessmentSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        obj = super().get_object()
        # Allow access only if the user owns the assessment or the session matches
        user = self.request.user
        session_key = self.request.session.session_key
        if obj.user != user and obj.session_key != session_key:
            self.permission_denied(self.request, message="You do not have access to this assessment.")
        return obj


class AssessmentPageView(TemplateView):
    template_name = "assessments/assessment_form.html"


def location_autocomplete(request):
    query = request.GET.get("q", "").strip()
    if not query or len(query) < 2:
        return JsonResponse([], safe=False)

    url = "https://api.geoapify.com/v1/geocode/autocomplete"
    params = {
        "text": query,
        "limit": 8,
        "format": "json",
        "filter": "countrycode:au",
        "apiKey": settings.GEOAPIFY_API_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
    except Exception:
        return JsonResponse([], safe=False)

    STATE_MAP = {
        "New South Wales": "NSW",
        "Victoria": "VIC",
        "Queensland": "QLD",
        "South Australia": "SA",
        "Western Australia": "WA",
        "Tasmania": "TAS",
        "Northern Territory": "NT",
        "Australian Capital Territory": "ACT",
    }

    results = []
    for item in data.get("results", []):
        postcode = item.get("postcode")
        city = item.get("city") or ""
        state = item.get("state") or ""
        suburb = item.get("suburb") or item.get("district") or item.get("neighbourhood") or ""
        lat = item.get("lat")
        lon = item.get("lon")
        state_short = STATE_MAP.get(state, state)
        location_name = suburb if suburb else city
        if not location_name:
            continue
        label = f"{location_name} {state_short} {postcode or ''}".strip()
        results.append({
            "label": label,
            "postcode": postcode,
            "city": city,
            "state": state_short,
            "suburb": suburb,
            "lat": lat,
            "lon": lon
        })

    return JsonResponse(results, safe=False)


class AssessmentSubmitView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [AllowAny]

    def post(self, request):
        # ---- Session management ----
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key

        # ---- Extract data ----
        # Special handling for 'documents' (multiple checkboxes)
        data = {}
        for key, value in request.data.items():
            if key == "documents":
                # DRF returns list for duplicate keys, but fallback to single value
                if hasattr(request.data, 'getlist'):
                    data[key] = request.data.getlist(key)
                elif isinstance(value, list):
                    data[key] = value
                else:
                    data[key] = [value] if value else []
            else:
                data[key] = value

        # Only allow valid model fields
        allowed_fields = {field.name for field in Assessment._meta.fields}
        clean_data = {k: v for k, v in data.items() if k in allowed_fields}
        clean_data["session_key"] = session_key
        if request.user.is_authenticated:
            clean_data["user"] = request.user

        # ---- Sanitize numeric fields ----
        decimal_fields = ["monthly_rent_budget", "household_income", "individual_income"]
        float_fields = ["lat", "lon"]
        int_fields = ["moving_with_adults", "moving_with_children", "moving_with_pets"]

        for field in decimal_fields:
            value = clean_data.get(field)
            if value in [None, "", "null"]:
                clean_data[field] = None
                continue
            try:
                cleaned = str(value).strip()
                if not re.match(r"^\d+(\.\d{1,2})?$", cleaned):
                    clean_data[field] = None
                    continue
                clean_data[field] = Decimal(cleaned)
            except (InvalidOperation, ValueError, TypeError):
                clean_data[field] = None

        for field in float_fields:
            value = clean_data.get(field)
            try:
                if value not in [None, "", "null"]:
                    clean_data[field] = float(str(value).strip())
                else:
                    clean_data[field] = None
            except (ValueError, TypeError):
                clean_data[field] = None

        for field in int_fields:
            value = clean_data.get(field)
            try:
                if value not in [None, "", "null"]:
                    clean_data[field] = int(str(value).strip())
                else:
                    clean_data[field] = 0
            except (ValueError, TypeError):
                clean_data[field] = 0

        # ---- Create assessment ----
        assessment = Assessment.objects.create(**clean_data)

        # ---- Scoring ----
        earned_points = 0
        total_possible = 0
        strengths = []
        weaknesses = []
        category_scores = {}

        # 1️⃣ Budget vs location
        budget_points = 0
        budget_max = 20
        try:
            monthly_budget = float(assessment.monthly_rent_budget or 0)
            suburb_median_rent = {
                "Sydney CBD": 3000, "Darling Harbour": 3200, "The Rocks": 3100,
                "Melbourne CBD": 2500, "Docklands": 2400, "Southbank": 2600,
                "Brisbane CBD": 2000, "Fortitude Valley": 2100,
            }
            median_rent = suburb_median_rent.get(assessment.suburb or "", 2500)
            # Fixed: budget must be >= median to be sufficient
            if monthly_budget >= median_rent:
                budget_points = 20
                strengths.append("Budget aligns with desired suburb")
            else:
                weaknesses.append("Budget may be insufficient for typical rent in this suburb")
        except (ValueError, TypeError):
            weaknesses.append("Budget not provided")
        earned_points += budget_points
        total_possible += budget_max
        category_scores["budget"] = int((budget_points / budget_max) * 100)

        # 2️⃣ Employment
        employment_points = 0
        employment_max = 20
        if assessment.employment_status in ["full_time", "self_employed"]:
            employment_points = 20
            strengths.append("Stable employment")
        else:
            weaknesses.append("Employment stability could be improved")
        earned_points += employment_points
        total_possible += employment_max
        category_scores["employment"] = int((employment_points / employment_max) * 100)

        # 3️⃣ Time in role
        tenure_points = 0
        tenure_max = 5
        try:
            parts = (assessment.time_in_role or "").split()
            number = int(parts[0])
            unit = parts[1].lower() if len(parts) > 1 else "months"
            if "year" in unit:
                months_in_role = number * 12
            elif "week" in unit:
                months_in_role = max(1, number // 4)
            else:
                months_in_role = number
            if months_in_role >= 12:
                tenure_points = 5
                strengths.append("Tenured in current role")
            else:
                weaknesses.append("Short tenure in current role")
        except (ValueError, IndexError):
            weaknesses.append("Time in role not provided")
        earned_points += tenure_points
        total_possible += tenure_max
        # No category score for tenure (optional)

        # 4️⃣ Rental history
        rental_points = 0
        rental_max = 10
        if assessment.rental_history in ["rented_locally", "owned_home"]:
            rental_points = 10
            strengths.append("Positive rental history")
        else:
            weaknesses.append("Limited rental history")
        earned_points += rental_points
        total_possible += rental_max
        category_scores["rental_history"] = int((rental_points / rental_max) * 100)

        # 5️⃣ Income vs rent
        income_points = 0
        income_max = 20
        try:
            household_income_annual = float(assessment.household_income or 0)
            if assessment.household_income_period == "monthly":
                household_income_annual *= 12
            elif assessment.household_income_period == "weekly":
                household_income_annual *= 52
            monthly_rent = float(assessment.monthly_rent_budget or 0)
            if household_income_annual > 0 and monthly_rent > 0:
                rent_ratio = monthly_rent / (household_income_annual / 12)
                if rent_ratio <= 0.3:
                    income_points = 20
                    strengths.append("Affordable rent relative to income")
                else:
                    weaknesses.append("Rent is high relative to income")
        except (ValueError, TypeError):
            weaknesses.append("Income information incomplete")
        earned_points += income_points
        total_possible += income_max
        category_scores["income"] = int((income_points / income_max) * 100)

        # 6️⃣ Documents
        docs_points = 0
        docs_max = 20
        num_docs = len(assessment.documents) if isinstance(assessment.documents, list) else 0
        docs_points = min(num_docs * 5, 20)
        if num_docs >= 3:
            strengths.append("Well-prepared documents")
        else:
            weaknesses.append("Insufficient documents for application")
        earned_points += docs_points
        total_possible += docs_max
        category_scores["documents"] = int((docs_points / docs_max) * 100)

        # 7️⃣ Proof of income
        proof_points = 0
        proof_max = 5
        if (assessment.proof_of_income or "").lower() != "none":
            proof_points = 5
            strengths.append("Proof of income provided")
        else:
            weaknesses.append("No proof of income provided")
        earned_points += proof_points
        total_possible += proof_max

        # 8️⃣ Household composition
        household_points = 0
        household_max = 5
        adults = assessment.moving_with_adults or 0
        children = assessment.moving_with_children or 0
        pets = assessment.moving_with_pets or 0
        total_people = adults + children
        if total_people <= 4 and pets <= 2:
            household_points = 5
            strengths.append("Household size manageable")
        else:
            weaknesses.append("Household size may impact readiness")
        earned_points += household_points
        total_possible += household_max
        category_scores["household"] = int((household_points / household_max) * 100)

        # Context issues penalty
        if assessment.context_issues not in [None, "", "None"]:
            weaknesses.append("History/context issues reported")
            earned_points -= 5

        # Final score (capped 0-100)
        score = int((earned_points / total_possible) * 100) if total_possible > 0 else 0
        score = max(0, min(score, 100))

        # Risk level
        if score >= 70:
            risk_level = "Low"
        elif score >= 40:
            risk_level = "Medium"
        else:
            risk_level = "High"

        # Gap analysis
        gaps, recommendations = generate_gap_analysis(assessment, category_scores)

        # Save results
        assessment.readiness_score = score
        assessment.risk_level = risk_level
        assessment.strengths = strengths
        assessment.weaknesses = weaknesses
        assessment.gap_analysis = gaps
        assessment.recommendations = recommendations
        assessment.save(update_fields=[
            "readiness_score", "risk_level", "strengths", "weaknesses",
            "gap_analysis", "recommendations"
        ])

        serializer = AssessmentSerializer(assessment)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ClaimLatestAssessmentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session_key = request.session.session_key
        if not session_key:
            return Response({"detail": "No session key."}, status=status.HTTP_400_BAD_REQUEST)

        assessment = Assessment.objects.filter(session_key=session_key).order_by("-created_at").first()
        if not assessment:
            return Response({"detail": "No assessment found in this session."}, status=status.HTTP_404_NOT_FOUND)

        if assessment.user_id is None:
            assessment.user = request.user
            assessment.save(update_fields=["user"])

        return Response({"detail": "Assessment claimed."}, status=status.HTTP_200_OK)