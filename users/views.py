from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from .serializers import LoginSerializer,SignupSerializer,PasswordResetRequestSerializer,ResetPasswordConfirmSerializer,UserSerializer

from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required



User = get_user_model()


# Login Page
def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard-home")

    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, "Login successful!")
            return redirect("home")
        else:
            messages.error(request, "Invalid credentials")

    return render(request, "users/login.html")




# Signup Page
def signup_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard-home")

    if request.method == "POST":
        full_name = request.POST.get("full_name")
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = User.objects.create_user(
            email=email,
            password=password,
            full_name=full_name
        )

        login(request, user)
        messages.success(request, "Signup successful! Welcome 🎉")
        return redirect("dashboard_home")

    return render(request, "users/register.html")
    



# Logout view

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect("login")




def forgot_password_view(request):
    if request.method == "POST":
        email = request.POST.get("email")

        try:
            user = User.objects.get(email=email)

            # Redirect to reset page with uid
            return redirect("reset-password-confirm", uid=user.id)

        except User.DoesNotExist:
            messages.error(request, "Email not found")

    return render(request, "users/forgot_password.html")





def reset_password_confirm_view(request, uid):
    try:
        user = User.objects.get(id=uid)
    except User.DoesNotExist:
        messages.error(request, "Invalid reset link")
        return redirect("login")

    if request.method == "POST":
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            messages.error(request, "Passwords do not match")
        else:
            user.set_password(password)
            user.save()

            messages.success(request, "Password reset successful. Please login.")
            return redirect("login")

    return render(request, "users/reset-password-confirm.html", {"uid": uid})