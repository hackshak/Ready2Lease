def normalize_income_to_annual(income, period):
    try:
        income = float(income or 0)
    except (ValueError, TypeError):
        income = 0

    if period == "weekly":
        return income * 52
    if period == "monthly":
        return income * 12
    return income


def parse_months_in_role(time_in_role: str) -> int:
    try:
        parts = (time_in_role or "").split()
        number = int(parts[0])
        unit = parts[1].lower() if len(parts) > 1 else "months"

        if "year" in unit:
            return number * 12
        if "week" in unit:
            return max(1, number // 4)
        return number
    except (ValueError, IndexError, TypeError):
        return 0


def risk_from_score(score: int) -> str:
    if score >= 70:
        return "Low"
    if score >= 40:
        return "Medium"
    return "High"


def build_detailed_breakdown(a):
    categories = []

    # Income strength
    landlord_income = [
        "Consistent income that covers rent comfortably",
        "Rent typically ≤ 30–35% of income",
        "Clear proof of income (payslips/bank statements)"
    ]
    why_income = []

    annual_income = normalize_income_to_annual(a.household_income, a.household_income_period)
    monthly_income = (annual_income / 12) if annual_income else 0
    monthly_rent = float(a.monthly_rent_budget or 0)

    if annual_income <= 0:
        score_income = 10
        explanation_income = "Income is missing or invalid, so affordability can’t be verified."
        why_income.append("Household income not provided.")
    elif monthly_rent <= 0:
        score_income = 20
        explanation_income = "Your rent target is missing, so affordability can’t be assessed."
        why_income.append("Monthly rent budget not provided.")
    else:
        rent_ratio = monthly_rent / monthly_income if monthly_income else 1
        pct = int(rent_ratio * 100)

        if rent_ratio <= 0.30:
            score_income = 85
            why_income.append(f"Rent is ~{pct}% of income (strong).")
        elif rent_ratio <= 0.35:
            score_income = 70
            why_income.append(f"Rent is ~{pct}% of income (acceptable).")
        elif rent_ratio <= 0.45:
            score_income = 50
            why_income.append(f"Rent is ~{pct}% of income (tight).")
        else:
            score_income = 30
            why_income.append(f"Rent is ~{pct}% of income (high risk).")

        explanation_income = "Income strength is mainly based on rent affordability relative to your household income."

    categories.append({
        "category": "income_strength",
        "score": score_income,
        "risk_level": risk_from_score(score_income),
        "explanation": explanation_income,
        "why_risk": why_income,
        "landlords_look_for": landlord_income
    })

    # Employment stability
    landlord_emp = [
        "Stable employment type (full-time tends to score highest)",
        "Longer tenure reduces perceived risk",
        "Verifiable details (employer + payslips)"
    ]
    why_emp = []

    emp = (a.employment_status or "").lower()
    months = parse_months_in_role(a.time_in_role)

    if emp == "full_time":
        score_emp = 80
        why_emp.append("Full-time employment.")
    elif emp == "self_employed":
        score_emp = 65
        why_emp.append("Self-employed (often requires stronger documentation).")
    elif emp:
        score_emp = 45
        why_emp.append(f"Employment is {emp.replace('_',' ')} (less stable).")
    else:
        score_emp = 20
        why_emp.append("Employment status missing.")

    if months >= 12:
        score_emp += 15
        why_emp.append("Tenure 12+ months.")
    elif 6 <= months < 12:
        score_emp += 8
        why_emp.append("Tenure 6–11 months.")
    elif 1 <= months < 6:
        score_emp += 3
        why_emp.append("Tenure under 6 months.")
    else:
        why_emp.append("Time in role missing or invalid.")

    score_emp = max(0, min(score_emp, 100))
    explanation_emp = "Employment stability is based on employment type and how long you’ve been in your role."

    categories.append({
        "category": "employment_stability",
        "score": score_emp,
        "risk_level": risk_from_score(score_emp),
        "explanation": explanation_emp,
        "why_risk": why_emp,
        "landlords_look_for": landlord_emp
    })

    # Rental history
    landlord_rental = [
        "Previous rentals with positive references",
        "No arrears/eviction history",
        "Consistency and reliability"
    ]
    why_rental = []

    rh = (a.rental_history or "").lower()
    if rh == "rented_locally":
        score_rental = 80
        why_rental.append("Rented locally (strong reference signal).")
        explanation_rental = "Local rental history usually provides verifiable references."
    elif rh == "owned_home":
        score_rental = 75
        why_rental.append("Previously owned a home (stability signal).")
        explanation_rental = "Ownership can signal stability, though rental references may be different."
    elif rh:
        score_rental = 45
        why_rental.append("Limited/non-standard rental history.")
        explanation_rental = "Limited rental history can reduce reference strength."
    else:
        score_rental = 30
        why_rental.append("Rental history missing.")
        explanation_rental = "Landlords typically want a clear rental track record or strong substitutes."

    if a.context_issues:
        score_rental = max(0, score_rental - 10)
        why_rental.append("Context/history issues reported.")

    categories.append({
        "category": "rental_history",
        "score": score_rental,
        "risk_level": risk_from_score(score_rental),
        "explanation": explanation_rental,
        "why_risk": why_rental,
        "landlords_look_for": landlord_rental
    })

    # Documentation readiness
    landlord_docs = [
        "Proof of income (payslips/bank statements)",
        "ID documents",
        "References (landlord/employer)",
        "Fast, complete submission"
    ]
    why_docs = []

    docs = a.documents if isinstance(a.documents, list) else []
    num_docs = len(docs)

    score_docs = min(num_docs * 20, 80)
    if num_docs >= 3:
        why_docs.append(f"{num_docs} documents selected (good).")
        explanation_docs = "Having key documents ready improves speed and credibility."
    else:
        why_docs.append(f"Only {num_docs} documents selected (missing items).")
        explanation_docs = "Missing documents can slow approval or lower confidence."

    poi = (a.proof_of_income or "").lower()
    if poi and poi != "none":
        score_docs += 20
        why_docs.append("Proof of income selected.")
    else:
        why_docs.append("No proof of income selected.")

    score_docs = max(0, min(score_docs, 100))

    categories.append({
        "category": "documentation_readiness",
        "score": score_docs,
        "risk_level": risk_from_score(score_docs),
        "explanation": explanation_docs,
        "why_risk": why_docs,
        "landlords_look_for": landlord_docs
    })

    # Overall competitiveness (weighted)
    landlord_overall = [
        "Affordability + stability + references",
        "Complete application with minimal friction",
        "Low perceived risk vs other applicants"
    ]
    why_overall = []

    income_score = categories[0]["score"]
    emp_score = categories[1]["score"]
    rental_score = categories[2]["score"]
    docs_score = categories[3]["score"]

    suburb_median_rent = {
        'Sydney CBD': 3000, 'Darling Harbour': 3200, 'The Rocks': 3100,
        'Melbourne CBD': 2500, 'Docklands': 2400, 'Southbank': 2600,
        'Brisbane CBD': 2000, 'Fortitude Valley': 2100
    }
    median_rent = suburb_median_rent.get(a.suburb or "", 2500)
    location_score = 70 if float(a.monthly_rent_budget or 0) <= median_rent else 40
    why_overall.append("Target rent compared to typical rent in your chosen suburb.")

    score_overall = round(
        income_score * 0.30 +
        emp_score * 0.25 +
        rental_score * 0.20 +
        docs_score * 0.15 +
        location_score * 0.10
    )

    if score_overall >= 70:
        why_overall.append("Overall signals are competitive for typical screening.")
    elif score_overall >= 40:
        why_overall.append("Moderately competitive—fixing 1–2 gaps can improve outcomes.")
    else:
        why_overall.append("Less competitive—address key gaps before applying widely.")

    explanation_overall = "Competitiveness estimates how strong your application looks against typical landlord screening expectations."

    categories.append({
        "category": "overall_competitiveness",
        "score": score_overall,
        "risk_level": risk_from_score(score_overall),
        "explanation": explanation_overall,
        "why_risk": why_overall,
        "landlords_look_for": landlord_overall
    })

    return categories