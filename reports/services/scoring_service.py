def calculate_score(assessment):

    score = 0

    strengths = []
    weaknesses = []
    recommendations = []
    gap_analysis = {}

    docs = assessment.documents or []

    # Identity Documents
    if "passport" in docs:
        score += 20
        strengths.append("Primary ID document provided")
    else:
        weaknesses.append("Missing primary ID document")
        recommendations.append("Upload passport or birth certificate")

    if "driver_license" in docs:
        score += 20
    else:
        weaknesses.append("Driver license not provided")
        recommendations.append("Upload driver license for stronger ID profile")

    # Income
    if assessment.household_income:
        score += 25
        strengths.append("Stable household income")
    else:
        weaknesses.append("No household income provided")
        recommendations.append("Provide proof of income")

    # Rental history
    if assessment.rental_history == "rented_locally":
        score += 20
        strengths.append("Local rental history")
    elif assessment.rental_history == "first_time_renter":
        weaknesses.append("No formal rental history")
        recommendations.append("Prepare employer or landlord references")

    # Income proof
    if assessment.proof_of_income == "recent_payslip":
        score += 15
    elif assessment.proof_of_income == "none":
        weaknesses.append("Income proof missing")
        recommendations.append("Upload payslip or bank statements")

    score = min(score, 100)

    # Gap analysis summary
    gap_analysis = {
        "missing_documents": [
            d for d in ["passport", "driver_license"] if d not in docs
        ],
        "income_verified": assessment.proof_of_income != "none",
        "rental_history": assessment.rental_history
    }

    # Save computed fields
    assessment.readiness_score = score
    assessment.strengths = strengths
    assessment.weaknesses = weaknesses
    assessment.recommendations = recommendations
    assessment.gap_analysis = gap_analysis

    return score