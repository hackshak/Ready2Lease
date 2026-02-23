from django.urls import path
from . import views

urlpatterns = [
    path("",views.home_page,name="home"),
    path("upgrade/",views.upgrade_page,name="upgrade_page")
]
