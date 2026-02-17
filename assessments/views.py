from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Assessment
from .serializers import AssessmentSerializer
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.conf import settings
import requests





class AssessmentPageView(TemplateView):
    template_name = "assessments/assessment_form.html"



import requests
from django.http import JsonResponse
from django.conf import settings

def location_autocomplete(request):
    query = request.GET.get("q", "").strip()

    if not query or len(query) < 2:
        return JsonResponse([], safe=False)

    url = "https://api.geoapify.com/v1/geocode/autocomplete"

    params = {
        "text": query,
        "limit": 8,
        "format": "json",
        "type": "postcode",  # Only postcode-level results
        "apiKey": settings.GEOAPIFY_API_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
    except Exception:
        return JsonResponse([], safe=False)

    results = []

    for item in data.get("results", []):
        if item.get("result_type") != "postcode":
            continue

        postcode = item.get("postcode")
        country_code = item.get("country_code")

        if not postcode:
            continue


        city = item.get("city") or ""
        state = item.get("state") or ""
        suburb = (
            item.get("suburb") or
            item.get("district") or
            item.get("neighbourhood") or
            ""
        )

        lat = item.get("lat")
        lon = item.get("lon")

        if suburb:
            label = f"{suburb}, {city} - {postcode}"
        else:
            label = f"{city}, {state} - {postcode}"

        results.append({
            "label": label,
            "postcode": postcode,
            "city": city,
            "state": state,
            "suburb": suburb,
            "lat": lat,
            "lon": lon
        })

    return JsonResponse(results, safe=False)







@method_decorator(csrf_exempt, name='dispatch')
class AssessmentSubmitView(APIView):
    def post(self, request):
        # --------- Session management ----------
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key

        data = request.data.copy()
        data['session_key'] = session_key

        # --------- Sanitize numeric fields ----------
        float_fields = ['lat', 'lon', 'monthly_rent_budget', 'household_income', 'individual_income']
        int_fields = ['moving_with_adults', 'moving_with_children', 'moving_with_pets']

        for field in float_fields:
            value = data.get(field)
            try:
                data[field] = float(str(value).strip()) if value not in [None, ''] else None
            except (ValueError, TypeError):
                data[field] = None

        for field in int_fields:
            value = data.get(field)
            try:
                data[field] = int(str(value).strip()) if value not in [None, ''] else 0
            except (ValueError, TypeError):
                data[field] = 0

        # --------- Save or update assessment ----------
        assessment, created = Assessment.objects.update_or_create(
            session_key=session_key,
            defaults=data
        )

        # --------- Scoring ----------
        score = 0
        strengths = []
        weaknesses = []

        # --- STEP 1: Budget vs location ---
        try:
            monthly_budget = float(assessment.monthly_rent_budget or 0)
            suburb_median_rent = {
                'Sydney CBD': 3000, 'Darling Harbour': 3200, 'The Rocks': 3100,
                'Melbourne CBD': 2500, 'Docklands': 2400, 'Southbank': 2600,
                'Brisbane CBD': 2000, 'Fortitude Valley': 2100
            }
            median_rent = suburb_median_rent.get(assessment.suburb or "", 2500)

            if monthly_budget <= median_rent:
                score += 20
                strengths.append('Budget aligns with desired suburb')
            else:
                weaknesses.append('Budget exceeds typical rent in desired suburb')
        except:
            weaknesses.append('Budget not provided')

        # --- STEP 2: Employment & rental history ---
        if assessment.employment_status in ['full_time', 'self_employed']:
            score += 20
            strengths.append('Stable employment')
        else:
            weaknesses.append('Employment stability could be improved')

        # --- Time in role (tenure) ---
        try:
            parts = (assessment.time_in_role or "").split()
            number = int(parts[0])
            unit = parts[1].lower() if len(parts) > 1 else "months"

            if "year" in unit:
                months_in_role = number * 12
            elif "week" in unit:
                months_in_role = max(1, number // 4)  # Approx weeks to months
            else:  # assume months
                months_in_role = number

            if months_in_role >= 12:
                score += 5
                strengths.append('Tenured in current role')
            else:
                weaknesses.append('Short tenure in current role')
        except:
            weaknesses.append('Time in role not provided')

        # --- Rental history ---
        if assessment.rental_history in ['rented_locally', 'owned_home']:
            score += 10
            strengths.append('Positive rental history')
        else:
            weaknesses.append('Limited rental history')

        # --- STEP 3: Income & Documents ---
        try:
            household_income_annual = float(assessment.household_income or 0)
            if assessment.household_income_period == 'monthly':
                household_income_annual *= 12
            elif assessment.household_income_period == 'weekly':
                household_income_annual *= 52

            monthly_rent = float(assessment.monthly_rent_budget or 0)
            if household_income_annual > 0:
                rent_ratio = monthly_rent / (household_income_annual / 12)
                if rent_ratio <= 0.3:
                    score += 20
                    strengths.append('Affordable rent relative to income')
                else:
                    weaknesses.append('Rent is high relative to income')
            else:
                weaknesses.append('Income not provided')
        except:
            weaknesses.append('Income information incomplete')

        # Documents
        num_docs = len(assessment.documents) if isinstance(assessment.documents, list) else 0
        score += min(num_docs * 5, 20)
        if num_docs >= 3:
            strengths.append('Well-prepared documents')
        else:
            weaknesses.append('Insufficient documents for application')

        # Proof of income
        if (assessment.proof_of_income or "").lower() != 'none':
            score += 5
            strengths.append('Proof of income provided')
        else:
            weaknesses.append('No proof of income provided')

        # --- STEP 4: Household composition ---
        adults = assessment.moving_with_adults or 0
        children = assessment.moving_with_children or 0
        pets = assessment.moving_with_pets or 0
        total_people = adults + children

        if total_people <= 4 and pets <= 2:  # adjust thresholds here if needed
            score += 5
            strengths.append('Household size manageable')
        else:
            weaknesses.append('Household size may impact readiness')

        # --- Context / history issues ---
        if assessment.context_issues:
            weaknesses.append('History/context issues reported')
            score -= 5

        # --- Clamp score & assign risk ---
        score = max(0, min(score, 100))

        if score >= 70:
            risk_level = 'Low'
        elif score >= 40:
            risk_level = 'Medium'
        else:
            risk_level = 'High'

        # --- Save calculated values ---
        assessment.readiness_score = score
        assessment.risk_level = risk_level
        assessment.strengths = strengths
        assessment.weaknesses = weaknesses
        assessment.save()

        serializer = AssessmentSerializer(assessment)
        return Response(serializer.data, status=status.HTTP_200_OK)
