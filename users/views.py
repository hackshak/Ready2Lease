from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .serializers import LoginSerializer,SignupSerializer,PasswordResetRequestSerializer,ResetPasswordConfirmSerializer


User = get_user_model()

# Login Page Render
def login_page(request):
    return render(request, "users/login.html")

# Login Api View
class LoginAPIView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data['user']

            refresh = RefreshToken.for_user(user)

            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "message": "Login successful"
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




# Signup Page Render
def register_page(request):
    return render(request,'users/register.html')


# Signup api view
class SignupAPIView(APIView):
    def post(self, request):
        serializer = SignupSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            refresh = RefreshToken.for_user(user)

            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "message": "Account created successfully"
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    




# # Render HTML page
# def forgot_password_page(request):
#     return render(request, "users/forgot_password.html")


# # API View
# class PasswordResetRequestAPIView(APIView):
#     def post(self, request):
#         serializer = PasswordResetRequestSerializer(data=request.data)

#         if serializer.is_valid():
#             uid = serializer.validated_data['uid']
#             token = serializer.validated_data['token']

#             reset_link = f"/reset-password-confirm/{uid}/{token}/"

#             return Response({
#                 "message": "Reset link generated",
#                 "reset_link": reset_link
#             }, status=status.HTTP_200_OK)

#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




# # Reset Password Confirm Page
# def reset_password_confirm_page(request, uid, token):
#     return render(request, "users/reset-password-confirm.html", {
#         "uid": uid,
#         "token": token
#     })



# # api view for rest password
# class ResetPasswordConfirmAPIView(APIView):
#     def post(self, request):
#         serializer = ResetPasswordConfirmSerializer(data=request.data)

#         if serializer.is_valid():
#             serializer.save()
#             return Response({
#                 "message": "Password reset successful"
#             }, status=status.HTTP_200_OK)

#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    




# Render forgot password page
def forgot_password_page(request):
    return render(request, "users/forgot_password.html")

# API: check if email exists and return uid
class PasswordResetRequestAPIView(APIView):
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
                return Response({"uid": user.id}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({"detail": "Email not found"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Render reset password page
def reset_password_confirm_page(request, uid):
    return render(request, "users/reset-password-confirm.html", {"uid": uid})

# API: reset password
class ResetPasswordConfirmAPIView(APIView):
    def post(self, request):
        serializer = ResetPasswordConfirmSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Password reset successful"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Logout view
class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Get refresh token from request body
            refresh_token = request.data.get("refresh_token")
            if refresh_token is None:
                return Response({"detail": "Refresh token required"}, status=status.HTTP_400_BAD_REQUEST)

            # Blacklist the token (invalidate it)
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({"detail": "Successfully logged out"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)