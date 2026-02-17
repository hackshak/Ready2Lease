from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_page, name='login'),           # frontend page
    path('api/login/', views.LoginAPIView.as_view(), name='api-login'),  # backend API

     path('signup/', views.register_page, name='signup'),              # frontend
    path('api/signup/', views.SignupAPIView.as_view(), name='api-signup'),  # backend

    path('api/logout/', views.LogoutAPIView.as_view(), name='api-logout'),

    path('password-reset/', views.forgot_password_page, name='reset-password'),
    path('api/password-reset/', views.PasswordResetRequestAPIView.as_view(), name='api-password-reset'),

    path('reset-password-confirm/<int:uid>/', views.reset_password_confirm_page, name='reset-password-confirm'),
    path('api/reset-password-confirm/', views.ResetPasswordConfirmAPIView.as_view(), name='api-reset-password-confirm'),
]
