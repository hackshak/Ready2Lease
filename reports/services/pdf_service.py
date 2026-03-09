from django.template.loader import render_to_string
from weasyprint import HTML
from django.core.files.base import ContentFile
from django.conf import settings
from .qr_service import generate_qr


def generate_pdf(report):
    # PDF CACHE CHECK
    if report.pdf_file:
        return report.pdf_file

    assessment = report.assessment

    qr = generate_qr(report.report_id)

    score = assessment.readiness_score or 0

    if score < 40:
        profile = "Low Profile"
    elif score < 70:
        profile = "Average Profile"
    else:
        profile = "Strong Profile"

    strengths = assessment.strengths or []
    risks = assessment.weaknesses or []
    actions = assessment.recommendations or []

    highlights = strengths[:2]

    rent_coverage = None

    if assessment.household_income and assessment.monthly_rent_budget:
        try:
            rent_coverage = round(
                (assessment.monthly_rent_budget / assessment.household_income) * 100,
                1
            )
        except Exception:
            rent_coverage = None

    context = {
        "report": report,
        "assessment": assessment,
        "qr_code_url": qr,

        "score": score,
        "profile": profile,

        "strengths": strengths,
        "risks": risks,
        "actions": actions,

        "strength_count": len(strengths),
        "risk_count": len(risks),
        "action_count": len(actions),

        "highlights": highlights,

        "rent_coverage": rent_coverage,
    }

    html = render_to_string(
        "reports/tenant_report.html",
        context
    )

    pdf = HTML(
        string=html,
        base_url=settings.MEDIA_ROOT
    ).write_pdf()

    pdf_file = ContentFile(pdf, name=f"{report.report_id}.pdf")

    # Save generated PDF for future downloads
    report.pdf_file.save(pdf_file.name, pdf_file)

    return report.pdf_file  