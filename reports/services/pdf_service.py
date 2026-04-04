import os
import base64
import math

from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from django.conf import settings

from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration

from .qr_service import generate_qr


# ─────────────────────────────────────────────────────────────────────────────
# PROFILE HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _profile_from_score(score):
    """Thresholds must match AssessmentSubmitView exactly."""
    if score >= 70:
        return "Strong Profile", "#28d17c"
    elif score >= 40:
        return "Average Profile", "#f7c948"
    else:
        return "Low Profile", "#ff5a7a"


# ─────────────────────────────────────────────────────────────────────────────
# SVG SCORE RING
#
# WeasyPrint does not support conic-gradient.
# We build an SVG arc and encode it as a base64 data-URI.
#
# IMPORTANT: this function returns a bare data-URI string —
#   data:image/svg+xml;base64,PHN2Zy...
#
# NOT wrapped in url(...).  The template must wrap it:
#   background-image: url("{{ score_ring_bg }}");
#
# If we return url('data:...') and the template also wraps it,
# WeasyPrint sees url(url('data:...')) and tries to open it as a
# filesystem path, causing the "No such file or directory" error.
# ─────────────────────────────────────────────────────────────────────────────

def _arc_path(cx, cy, r, start_deg, end_deg):
    """SVG arc path d-string, clockwise from 12 o'clock."""
    start = math.radians(start_deg - 90)
    end   = math.radians(end_deg   - 90)
    x1 = cx + r * math.cos(start)
    y1 = cy + r * math.sin(start)
    x2 = cx + r * math.cos(end)
    y2 = cy + r * math.sin(end)
    large = 1 if (end_deg - start_deg) > 180 else 0
    return f"M {x1:.3f} {y1:.3f} A {r} {r} 0 {large} 1 {x2:.3f} {y2:.3f}"


def _ring_svg_data_uri(score, color, bg_color="#111e3c", size=140, stroke=10):
    """
    Return a bare base64 data-URI (no url() wrapper).
    Template usage:  background-image: url("{{ score_ring_bg }}");
    """
    cx = cy = size / 2
    r  = cx - stroke

    filled_deg = max(0, min(score, 100)) / 100 * 360

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{size}" height="{size}" viewBox="0 0 {size} {size}">',
        f'<circle cx="{cx}" cy="{cy}" r="{r - stroke // 2 - 1}" fill="{bg_color}"/>',
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" '
        f'stroke="rgba(255,255,255,0.08)" stroke-width="{stroke}"/>',
    ]

    if filled_deg > 0:
        if filled_deg >= 359.9:
            parts.append(
                f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" '
                f'stroke="{color}" stroke-width="{stroke}"/>'
            )
        else:
            d = _arc_path(cx, cy, r, 0, filled_deg)
            parts.append(
                f'<path d="{d}" fill="none" stroke="{color}" '
                f'stroke-width="{stroke}" stroke-linecap="round"/>'
            )

    parts.append("</svg>")
    encoded = base64.b64encode("".join(parts).encode()).decode()
    # Bare data-URI — no url() here; the template adds url("...")
    return f"data:image/svg+xml;base64,{encoded}"


# ─────────────────────────────────────────────────────────────────────────────
# LOGO LOADER
# ─────────────────────────────────────────────────────────────────────────────

def _logo_data_uri():
    """
    Find Main.Logo.png and return it as a bare data-URI.
    Returns empty string if not found — template guards with {% if logo_data_uri %}.

    Add to settings.py to specify an explicit path:
        REPORT_LOGO_PATH = "/absolute/path/to/Main.Logo.png"
    """
    candidates = []

    explicit = getattr(settings, "REPORT_LOGO_PATH", None)
    if explicit:
        candidates.append(explicit)

    for static_dir in getattr(settings, "STATICFILES_DIRS", []):
        candidates.append(os.path.join(str(static_dir), "images", "Main.Logo.png"))

    candidates += [
        os.path.join(str(settings.BASE_DIR), "static",      "images", "Main.Logo.png"),
        os.path.join(str(settings.BASE_DIR), "staticfiles", "images", "Main.Logo.png"),
    ]

    for path in candidates:
        if os.path.isfile(path):
            with open(path, "rb") as fh:
                data = base64.b64encode(fh.read()).decode()
            ext  = os.path.splitext(path)[1].lstrip(".").lower()
            mime = "image/png" if ext == "png" else f"image/{ext}"
            return f"data:{mime};base64,{data}"

    return ""


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def generate_pdf(report, force_regenerate=False):
    """
    Build the tenant dossier PDF for *report*.

    Parameters
    ----------
    report           : TenantReport
    force_regenerate : bool
        Delete and rebuild any cached PDF so the latest score is reflected.
    """

    if report.pdf_file and not force_regenerate:
        return report.pdf_file

    # Delete stale file
    if report.pdf_file:
        try:
            old = report.pdf_file.path
            if os.path.exists(old):
                os.remove(old)
        except Exception:
            pass
        report.pdf_file = None
        report.save(update_fields=["pdf_file"])

    assessment = report.assessment
    qr         = generate_qr(report.report_id)
    score      = report.score or 0

    profile, profile_color = _profile_from_score(score)

    strengths = report.strengths or []
    risks     = report.risks     or []
    actions   = report.actions   or []

    # Rent-to-income ratio
    rent_coverage = None
    if assessment.household_income and assessment.monthly_rent_budget:
        try:
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

    context = {
        "report":      report,
        "assessment":  assessment,
        "qr_code_url": qr,

        "score":         score,
        "score_deg":     round((score / 100) * 360),
        "profile":       profile,
        "profile_color": profile_color,

        # Bare data-URIs — template wraps each in url("...") in CSS
        "score_ring_bg": _ring_svg_data_uri(score, profile_color, bg_color="#111e3c"),
        "mini_ring_bg":  _ring_svg_data_uri(score, profile_color, bg_color="#f5f7fc", size=80, stroke=7),

        "strengths":      strengths,
        "risks":          risks,
        "actions":        actions,
        "strength_count": len(strengths),
        "risk_count":     len(risks),
        "action_count":   len(actions),
        "highlights":     strengths[:3],
        "rent_coverage":  rent_coverage,

        "logo_data_uri":  _logo_data_uri(),
    }

    html_string = render_to_string("reports/tenant_report.html", context)

    font_config = FontConfiguration()

    pdf_bytes = HTML(
        string=html_string,
        base_url=settings.MEDIA_ROOT,
    ).write_pdf(font_config=font_config)

    pdf_file = ContentFile(pdf_bytes, name=f"{report.report_id}.pdf")
    report.pdf_file.save(pdf_file.name, pdf_file)

    return report.pdf_file