from django.template.loader import render_to_string
from weasyprint import HTML
from io import BytesIO


class CoverLetterPDFService:

    def generate_pdf(self, letter):

        paragraphs = [
            p.strip() for p in (letter.final_content or "").split("\n")
            if p.strip()
        ]

        html_string = render_to_string(
            "cover_letters/pdf.html",
            {
                "paragraphs": paragraphs,
                "user": letter.user,
                "date": letter.created_at.strftime("%d %B %Y"),
            }
        )

        pdf_file = BytesIO()
        HTML(string=html_string).write_pdf(pdf_file)
        pdf_file.seek(0)

        return pdf_file