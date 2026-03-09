def generate_analysis(assessment):

    strengths = []
    risks = []

    if assessment.household_income:
        strengths.append("Stable household income")

    if assessment.rental_history == "rented_locally":
        strengths.append("Local rental history")

    if "passport" in assessment.documents:
        strengths.append("Primary ID document provided")

    if not assessment.documents:
        risks.append("No identity documentation")

    if assessment.rental_history == "first_time_renter":
        risks.append("No rental history")

    if assessment.proof_of_income == "none":
        risks.append("Income proof missing")

    return strengths, risks