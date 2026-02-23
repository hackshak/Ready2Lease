from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import FileResponse

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import CoverLetter
from .serializers import (
    CoverLetterCreateSerializer,
    CoverLetterDetailSerializer,
    CoverLetterUpdateSerializer,
)
from .services.generator import CoverLetterGeneratorService
from .services.pdf import CoverLetterPDFService


# ==========================================================
# HELPER
# ==========================================================

def require_premium(user):
    return getattr(user, "is_premium", False)


# ==========================================================
# TEMPLATE VIEWS (VISIBLE TO ALL LOGGED-IN USERS)
# ==========================================================

@login_required
def cover_letter_list_view(request):
    # ✅ Page visible to all logged-in users
    return render(
        request,
        "cover_letters/list.html",
        {
            "is_premium": require_premium(request.user)
        }
    )


@login_required
def cover_letter_editor_view(request, pk):
    # ✅ Page visible to all logged-in users
    letter = get_object_or_404(
        CoverLetter,
        pk=pk,
        user=request.user
    )

    return render(
        request,
        "cover_letters/editor.html",
        {
            "letter_id": letter.id,
            "is_premium": require_premium(request.user)
        }
    )


# ==========================================================
# API: LIST LETTERS (PREMIUM FUNCTIONALITY)
# ==========================================================

class CoverLetterListAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        if not require_premium(request.user):
            return Response(
                {"detail": "Premium required"},
                status=status.HTTP_403_FORBIDDEN
            )

        letters = CoverLetter.objects.filter(
            user=request.user
        ).order_by("-created_at")

        data = [
            {
                "id": letter.id,
                "property_address": letter.property_address,
                "employment_type": letter.employment_type,
                "rental_history_type": letter.rental_history_type,
                "created_at": letter.created_at,
            }
            for letter in letters
        ]

        return Response(data)


# ==========================================================
# API: GENERATE NEW LETTER (PREMIUM FUNCTIONALITY)
# ==========================================================

class GenerateCoverLetterAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        if not require_premium(request.user):
            return Response(
                {"detail": "Premium required"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = CoverLetterCreateSerializer(data={
            "property_address": request.data.get("property_address"),
            "tone": request.data.get("tone"),
            "employment_type": request.data.get("employment_type"),
            "rental_history_type": request.data.get("rental_history_type"),
            "base_inputs": {
                "name": request.data.get("name"),
                "employment_info": request.data.get("employment_info"),
                "income": request.data.get("income"),
                "rental_history": request.data.get("rental_history"),
                "custom_note": request.data.get("custom_note"),
            }
        })

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        validated_data = serializer.validated_data
        generator = CoverLetterGeneratorService()

        try:
            generated_text = generator.generate_letter(
                base_inputs=validated_data["base_inputs"],
                tone=validated_data["tone"],
                property_address=validated_data.get("property_address"),
            )
        except Exception as e:
            return Response({"error": str(e)}, status=500)

        letter = CoverLetter.objects.create(
            user=request.user,
            property_address=validated_data.get("property_address"),
            tone=validated_data.get("tone"),
            employment_type=validated_data.get("employment_type"),
            rental_history_type=validated_data.get("rental_history_type"),
            base_inputs=validated_data.get("base_inputs"),
            generated_content=generated_text,
            edited_content=generated_text,
            status="generated",
        )

        return Response({
            "id": letter.id,
            "generated_content": generated_text
        })


# ==========================================================
# API: GET LETTER DETAIL (PREMIUM FUNCTIONALITY)
# ==========================================================

class CoverLetterDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):

        if not require_premium(request.user):
            return Response(
                {"detail": "Premium required"},
                status=status.HTTP_403_FORBIDDEN
            )

        letter = get_object_or_404(
            CoverLetter,
            pk=pk,
            user=request.user
        )

        serializer = CoverLetterDetailSerializer(letter)
        return Response(serializer.data)


# ==========================================================
# API: SAVE EDITED CONTENT (PREMIUM FUNCTIONALITY)
# ==========================================================

class SaveCoverLetterAPI(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):

        if not require_premium(request.user):
            return Response(
                {"detail": "Premium required"},
                status=status.HTTP_403_FORBIDDEN
            )

        letter = get_object_or_404(
            CoverLetter,
            pk=pk,
            user=request.user
        )

        serializer = CoverLetterUpdateSerializer(
            letter,
            data=request.data,
            partial=True
        )

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        serializer.save()

        return Response({"success": True})


# ==========================================================
# API: EXPORT PDF (PREMIUM FUNCTIONALITY)
# ==========================================================

class ExportCoverLetterPDFAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):

        if not require_premium(request.user):
            return Response(
                {"detail": "Premium required"},
                status=status.HTTP_403_FORBIDDEN
            )

        letter = get_object_or_404(
            CoverLetter,
            pk=pk,
            user=request.user
        )

        if not letter.final_content:
            return Response(
                {"error": "No content available"},
                status=400
            )

        pdf_service = CoverLetterPDFService()
        pdf_file = pdf_service.generate_pdf(letter)

        return FileResponse(
            pdf_file,
            as_attachment=True,
            filename=f"cover_letter_{letter.id}.pdf",
        )