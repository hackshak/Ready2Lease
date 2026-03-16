from django.template.loader import render_to_string
from weasyprint import HTML
from django.core.files.base import ContentFile
from django.conf import settings
from .qr_service import generate_qr
import os


def generate_pdf(report):
    # PDF CACHE CHECK — return existing file if already generated
    if report.pdf_file:
        return report.pdf_file

    assessment = report.assessment

    qr = generate_qr(report.report_id)
    score = report.score or 0

    if score < 40:
        profile = "Low Profile"
        profile_color = "#ff5a7a"
    elif score < 70:
        profile = "Average Profile"
        profile_color = "#f7c948"
    else:
        profile = "Strong Profile"
        profile_color = "#28d17c"

    strengths = report.strengths or []
    risks = report.risks or []
    actions = report.actions or []

    highlights = strengths[:3]

    # Rent-to-income coverage ratio
    rent_coverage = None
    if assessment.household_income and assessment.monthly_rent_budget:
        try:
            # Normalise household income to monthly for comparison
            income = float(assessment.household_income)
            period = assessment.household_income_period or "monthly"
            if period == "annual":
                monthly_income = income / 12
            elif period == "weekly":
                monthly_income = income * 52 / 12
            else:
                monthly_income = income

            rent_coverage = round(
                (float(assessment.monthly_rent_budget) / monthly_income) * 100, 1
            )
        except Exception:
            rent_coverage = None

    # Score ring: degrees for CSS conic-gradient
    score_deg = round((score / 100) * 360)

    context = {
        "report": report,
        "assessment": assessment,
        "qr_code_url": qr,

        "score": score,
        "score_deg": score_deg,
        "profile": profile,
        "profile_color": profile_color,

        "strengths": strengths,
        "risks": risks,
        "actions": actions,

        "strength_count": len(strengths),
        "risk_count": len(risks),
        "action_count": len(actions),

        "highlights": highlights,
        "rent_coverage": rent_coverage,
        "logo_path": os.path.join(settings.BASE_DIR, "static", "images", "Main.Logo.png"),
    }

    html_string = render_to_string("reports/tenant_report.html", context)

    pdf_bytes = HTML(
        string=html_string,
        base_url=settings.MEDIA_ROOT,
    ).write_pdf()

    pdf_file = ContentFile(pdf_bytes, name=f"{report.report_id}.pdf")

    # Save generated PDF for future downloads
    report.pdf_file.save(pdf_file.name, pdf_file)

    return report.pdf_file