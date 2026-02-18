from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .serializers import LoginSerializer,SignupSerializer,PasswordResetRequestSerializer,ResetPasswordConfirmSerializer,UserSerializer

from django.contrib.auth import authenticate, login, logout


User = get_user_model()

# Login Page Render
def login_page(request):
    return render(request, "users/login.html")

# Login Api View
class LoginAPIView(APIView):
    authentication_classes = []  # Allow login without auth
    permission_classes = []

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)  # ✅ Creates session
            return Response({"message": "Login successful"}, status=200)

        return Response({"error": "Invalid credentials"}, status=400)




# Signup Page Render
def register_page(request):
    return render(request,'users/register.html')


# Signup api view
class SignupAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = SignupSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            # ✅ Automatically log the user in
            login(request, user)

            return Response(
                {"message": "Account created successfully"},
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


# Logged in user details
class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    




# Render forgot password page
def forgot_password_page(request):
    return render(request, "users/forgot_password.html")



# Password Reset Rquest Api view
class PasswordResetRequestAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data['email']

            try:
                user = User.objects.get(email=email)

                # ⚠️ For now returning UID (later you should use token)
                return Response(
                    {"uid": user.id},
                    status=status.HTTP_200_OK
                )

            except User.DoesNotExist:
                return Response(
                    {"detail": "Email not found"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    



# Render reset password page
def reset_password_confirm_page(request, uid):
    return render(request, "users/reset-password-confirm.html", {"uid": uid})





# Confirm Password Resr
class ResetPasswordConfirmAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = ResetPasswordConfirmSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()

            return Response(
                {"message": "Password reset successful"},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




# Logout view
class LogoutAPIView(APIView):
    def post(self, request):
        logout(request)  # ✅ destroys session

        return Response(
            {"message": "Logged out successfully"},
            status=status.HTTP_200_OK
        )