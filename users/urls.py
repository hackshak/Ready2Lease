from django.urls import path
from . import views

urlpatterns = [
    # logged in user details
    path('me/', views.CurrentUserView.as_view(), name='current-user'),

    path('login/', views.login_page, name='login'),          
    path('signup/', views.register_page, name='signup'),              
    path('api/login/', views.LoginAPIView.as_view(), name='api-login'),  
    path('api/logout/', views.LogoutAPIView.as_view(), name='api-logout'),
    path('api/signup/', views.SignupAPIView.as_view(), name='api-signup'), 
    path('api/password-reset/', views.PasswordResetRequestAPIView.as_view(), name='api-password-reset'),
    path('api/reset-password-confirm/', views.ResetPasswordConfirmAPIView.as_view(), name='api-reset-password-confirm'),
    path('password-reset/', views.forgot_password_page, name='reset-password'),
    path('reset-password-confirm/<int:uid>/', views.reset_password_confirm_page, name='reset-password-confirm'),




]
