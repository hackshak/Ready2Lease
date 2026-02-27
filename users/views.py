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
from django.core.validators import validate_email
from django.core.exceptions import ValidationError



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
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

def signup_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard-home")

    if request.method == "POST":
        full_name = request.POST.get("full_name")
        email = request.POST.get("email")
        password = request.POST.get("password")

        # 🔐 Email format validation
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "Please enter a valid email address.")
            return redirect("signup")

        # 🔐 Check duplicate email
        if User.objects.filter(email=email).exists():
            messages.error(request, "An account with this email already exists.")
            return redirect("signup")

        # 🔐 Password validation
        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return redirect("signup")

        # Split name
        name_parts = full_name.split()
        first_name = name_parts[0]
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        login(request, user)
        messages.success(request, "Signup successful! Welcome 🎉")
        return redirect("home")

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