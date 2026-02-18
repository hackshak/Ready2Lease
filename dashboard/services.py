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

    # -------------------------
    # Income strength
    # -------------------------
    landlord = [
        "Consistent income that covers rent comfortably",
        "Rent typically ≤ 30–35% of income",
        "Clear proof of income (payslips/bank statements)"
    ]
    why = []

    annual_income = normalize_income_to_annual(a.household_income, a.household_income_period)
    monthly_income = (annual_income / 12) if annual_income else 0
    monthly_rent = float(a.monthly_rent_budget or 0)

    if annual_income <= 0:
        score = 10
        explanation = "Income is missing or invalid, so affordability can’t be verified."
        why.append("Household income not provided.")
    elif monthly_rent <= 0:
        score = 20
        explanation = "Your rent target is missing, so affordability can’t be assessed."
        why.append("Monthly rent budget not provided.")
    else:
        rent_ratio = monthly_rent / monthly_income if monthly_income else 1
        pct = int(rent_ratio * 100)

        if rent_ratio <= 0.30:
            score = 85
            why.append(f"Rent is ~{pct}% of income (strong).")
        elif rent_ratio <= 0.35:
            score = 70
            why.append(f"Rent is ~{pct}% of income (acceptable).")
        elif rent_ratio <= 0.45:
            score = 50
            why.append(f"Rent is ~{pct}% of income (tight).")
        else:
            score = 30
            why.append(f"Rent is ~{pct}% of income (high risk).")

        explanation = "Income strength is mainly based on rent affordability relative to your household income."

    categories.append({
        "category": "income_strength",
        "score": score,
        "risk_level": risk_from_score(score),
        "explanation": explanation,
        "why_risk": why,
        "landlords_look_for": landlord
    })

    # -------------------------
    # Employment stability
    # -------------------------
    landlord = [
        "Stable employment type (full-time tends to score highest)",
        "Longer tenure reduces perceived risk",
        "Verifiable details (employer + payslips)"
    ]
    why = []

    emp = (a.employment_status or "").lower()
    months = parse_months_in_role(a.time_in_role)

    if emp == "full_time":
        score = 80
        why.append("Full-time employment.")
    elif emp == "self_employed":
        score = 65
        why.append("Self-employed (often requires stronger documentation).")
    elif emp:
        score = 45
        why.append(f"Employment is {emp.replace('_',' ')} (less stable).")
    else:
        score = 20
        why.append("Employment status missing.")

    if months >= 12:
        score += 15
        why.append("Tenure 12+ months.")
    elif 6 <= months < 12:
        score += 8
        why.append("Tenure 6–11 months.")
    elif 1 <= months < 6:
        score += 3
        why.append("Tenure under 6 months.")
    else:
        why.append("Time in role missing or invalid.")

    score = max(0, min(score, 100))
    explanation = "Employment stability is based on employment type and how long you’ve been in your role."

    categories.append({
        "category": "employment_stability",
        "score": score,
        "risk_level": risk_from_score(score),
        "explanation": explanation,
        "why_risk": why,
        "landlords_look_for": landlord
    })

    # -------------------------
    # Rental history
    # -------------------------
    landlord = [
        "Previous rentals with positive references",
        "No arrears/eviction history",
        "Consistency and reliability"
    ]
    why = []

    rh = (a.rental_history or "").lower()
    if rh == "rented_locally":
        score = 80
        why.append("Rented locally (strong reference signal).")
        explanation = "Local rental history usually provides verifiable references."
    elif rh == "owned_home":
        score = 75
        why.append("Previously owned a home (stability signal).")
        explanation = "Ownership can signal stability, though rental references may be different."
    elif rh:
        score = 45
        why.append("Limited/non-standard rental history.")
        explanation = "Limited rental history can reduce reference strength."
    else:
        score = 30
        why.append("Rental history missing.")
        explanation = "Landlords typically want a clear rental track record or strong substitutes."

    # optional: context issues can reduce confidence
    if a.context_issues:
        score = max(0, score - 10)
        why.append("Context/history issues reported.")

    categories.append({
        "category": "rental_history",
        "score": score,
        "risk_level": risk_from_score(score),
        "explanation": explanation,
        "why_risk": why,
        "landlords_look_for": landlord
    })

    # -------------------------
    # Documentation readiness
    # -------------------------
    landlord = [
        "Proof of income (payslips/bank statements)",
        "ID documents",
        "References (landlord/employer)",
        "Fast, complete submission"
    ]
    why = []

    docs = a.documents if isinstance(a.documents, list) else []
    num_docs = len(docs)

    # 0–80 from docs count
    score = min(num_docs * 20, 80)
    if num_docs >= 3:
        why.append(f"{num_docs} documents selected (good).")
        explanation = "Having key documents ready improves speed and credibility."
    else:
        why.append(f"Only {num_docs} documents selected (missing items).")
        explanation = "Missing documents can slow approval or lower confidence."

    poi = (a.proof_of_income or "").lower()
    if poi and poi != "none":
        score += 20
        why.append("Proof of income selected.")
    else:
        why.append("No proof of income selected.")

    score = max(0, min(score, 100))

    categories.append({
        "category": "documentation_readiness",
        "score": score,
        "risk_level": risk_from_score(score),
        "explanation": explanation,
        "why_risk": why,
        "landlords_look_for": landlord
    })

    # -------------------------
    # Overall competitiveness (weighted)
    # -------------------------
    landlord = [
        "Affordability + stability + references",
        "Complete application with minimal friction",
        "Low perceived risk vs other applicants"
    ]
    why = []

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
    why.append("Target rent compared to typical rent in your chosen suburb.")

    score = round(
        income_score * 0.30 +
        emp_score * 0.25 +
        rental_score * 0.20 +
        docs_score * 0.15 +
        location_score * 0.10
    )

    if score >= 70:
        why.append("Overall signals are competitive for typical screening.")
    elif score >= 40:
        why.append("Moderately competitive—fixing 1–2 gaps can improve outcomes.")
    else:
        why.append("Less competitive—address key gaps before applying widely.")

    explanation = "Competitiveness estimates how strong your application looks against typical landlord screening expectations."

    categories.append({
        "category": "overall_competitiveness",
        "score": score,
        "risk_level": risk_from_score(score),
        "explanation": explanation,
        "why_risk": why,
        "landlords_look_for": landlord
    })

    return categories




