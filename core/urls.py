from django.urls import path
from . import views

urlpatterns = [
    path("",views.home_page,name="home"),
    path("upgrade/",views.upgrade_page,name="upgrade_page"),
    path('privacy/',views.privacy_page,name="privacy_page"),
    path('terms/',views.terms_page,name="terms_page")
]
