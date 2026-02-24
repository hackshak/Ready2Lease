from django.shortcuts import render

# Create your views here.
def home_page(request):
    return render(request,"core/home.html")


def upgrade_page(request):
    return render(request,"core/upgrade.html")


def privacy_page(request):
    return render(request,"core/privacy_terms.html")


def terms_page(request):
    return render(request,"core/terms_page.html")