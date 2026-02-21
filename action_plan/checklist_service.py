from .models import UserDocument, ReferenceLetter, CoverLetter


class ChecklistService:

    DOCUMENTS_META = {
        "id_document": {
            "title": "ID Document",
            "description": "Used to verify your identity."
        },
        "payslip": {
            "title": "Payslip",
            "description": "Shows proof of income stability."
        },
        "bank_statement": {
            "title": "Bank Statement",
            "description": "Demonstrates financial credibility."
        },
        "reference_letter": {
            "title": "Reference Letter",
            "description": "Strengthens trust with landlord/employer."
        },
        "cover_letter": {
            "title": "Cover Letter",
            "description": "A compelling personal application letter."
        }
    }

    @staticmethod
    def get_checklist_for_assessment(user, assessment):

        checklist = []

        # Document types stored in UserDocument
        for doc_type in ["id_document", "payslip", "bank_statement"]:
            doc = UserDocument.objects.filter(
                user=user,
                assessment=assessment,
                document_type=doc_type
            ).first()

            checklist.append({
                "key": doc_type,
                "title": ChecklistService.DOCUMENTS_META[doc_type]["title"],
                "description": ChecklistService.DOCUMENTS_META[doc_type]["description"],
                "uploaded": bool(doc),
                "file_url": doc.file.url if doc else None,
                "object_id": doc.id if doc else None,
                "type": "document"
            })

        # Reference Letter
        ref = ReferenceLetter.objects.filter(
            user=user,
            assessment=assessment
        ).first()

        checklist.append({
            "key": "reference_letter",
            "title": ChecklistService.DOCUMENTS_META["reference_letter"]["title"],
            "description": ChecklistService.DOCUMENTS_META["reference_letter"]["description"],
            "uploaded": bool(ref),
            "file_url": ref.file.url if ref and ref.file else None,
            "object_id": ref.id if ref else None,
            "type": "reference"
        })

        # ------------------------------------------------
        # Cover Letter (FILE ONLY)
        # ------------------------------------------------
        cover = CoverLetter.objects.filter(
            user=user,
            assessment=assessment
        ).first()

        checklist.append({
            "key": "cover_letter",
            "title": ChecklistService.DOCUMENTS_META["cover_letter"]["title"],
            "description": ChecklistService.DOCUMENTS_META["cover_letter"]["description"],
            "uploaded": bool(cover and cover.file),
            "file_url": cover.file.url if cover and cover.file else None,
            "object_id": cover.id if cover else None,
            "type": "cover_letter"
        })

        total = len(checklist)
        completed = sum(1 for item in checklist if item["uploaded"])
        percentage = int((completed / total) * 100)

        return {
            "checklist": checklist,
            "completed": completed,
            "total": total,
            "percentage": percentage
        }