def normalize_income(amount, period):
    if not amount:
        return 0

    if period == "weekly":
        return amount * 52
    if period == "monthly":
        return amount * 12
    return amount  # annual


def generate_gap_analysis(assessment, category_scores):
    gaps = {}
    recommendations = []

    # -------------------------
    # 1️⃣ Income Gap
    # -------------------------
    annual_income = normalize_income(
        assessment.household_income or assessment.individual_income,
        assessment.household_income_period or assessment.individual_income_period
    )

    if category_scores.get("income", 0) < 50:
        gaps["income"] = "Income may be insufficient relative to rent budget."

        recommendations.append({
            "category": "income",
            "priority": "high",
            "suggestion": "Consider adding a guarantor to strengthen your application."
        })

        recommendations.append({
            "category": "income",
            "priority": "medium",
            "suggestion": "Provide 3+ recent payslips and consistent bank statements."
        })

    # -------------------------
    # 2️⃣ Rental History Gap
    # -------------------------
    if assessment.rental_history == "first_time_renter":
        gaps["rental_history"] = "No rental history found."

        recommendations.append({
            "category": "rental_history",
            "priority": "high",
            "suggestion": "Provide a character reference or employer reference."
        })

        recommendations.append({
            "category": "rental_history",
            "priority": "medium",
            "suggestion": "Offer additional upfront rent if possible."
        })

    # -------------------------
    # 3️⃣ Employment Gap
    # -------------------------
    if assessment.employment_status in ["part_time", "self_employed", "student"]:
        gaps["employment"] = "Employment stability may require additional proof."

        recommendations.append({
            "category": "employment",
            "priority": "medium",
            "suggestion": "Attach employment contract or employer letter."
        })

        recommendations.append({
            "category": "employment",
            "priority": "medium",
            "suggestion": "Provide last 3 months bank statements."
        })

    # -------------------------
    # 4️⃣ Documents Gap
    # -------------------------
    if not assessment.documents or len(assessment.documents) < 2:
        gaps["documents"] = "Limited supporting documents uploaded."

        recommendations.append({
            "category": "documents",
            "priority": "medium",
            "suggestion": "Upload at least 2 ID documents (passport, driver license)."
        })

    # -------------------------
    # 5️⃣ Proof of Income Gap
    # -------------------------
    if assessment.proof_of_income == "none":
        gaps["proof_of_income"] = "No proof of income provided."

        recommendations.append({
            "category": "proof_of_income",
            "priority": "high",
            "suggestion": "Upload recent payslips or bank statements."
        })

    # -------------------------
    # 6️⃣ Household Risk
    # -------------------------
    if assessment.moving_with_pets and assessment.moving_with_pets > 1:
        recommendations.append({
            "category": "pets",
            "priority": "low",
            "suggestion": "Prepare pet references and vaccination records."
        })

    return gaps, recommendations
