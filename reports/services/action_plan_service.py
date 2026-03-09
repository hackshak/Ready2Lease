def generate_actions(assessment):

    actions = []

    docs = assessment.documents or []

    if "passport" not in docs:
        actions.append({
            "timeline": "today",
            "title": "Upload Passport Or Birth Certificate",
            "description": "This is a blocker. Agents cannot process without it."
        })

    if "driver_license" not in docs:
        actions.append({
            "timeline": "this_week",
            "title": "Upload Driver License For Stronger ID Profile",
            "description": "Driver license improves your identity score."
        })

    if assessment.proof_of_income == "none":
        actions.append({
            "timeline": "this_week",
            "title": "Upload Proof Of Income",
            "description": "Provide payslip or bank statement."
        })

    if assessment.rental_history == "first_time_renter":
        actions.append({
            "timeline": "next_week",
            "title": "Prepare References",
            "description": "Ask employer or landlord to verify."
        })

    return actions