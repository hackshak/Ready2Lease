from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),
    path("logout/", views.logout_view, name="logout"),
    path("password-reset/", views.forgot_password_view, name="reset-password"),
    path("reset-password-confirm/<int:uid>/", views.reset_password_confirm_view, name="reset-password-confirm"),

]
