from django.urls import path
from . import views 

urlpatterns = [
    path('assessment/', views.AssessmentPageView.as_view(), name='assessment-page'),
    path('api/location-autocomplete/', views.location_autocomplete, name='location-autocomplete'),
    path('api/assessment/submit/', views.AssessmentSubmitView.as_view(), name='assessment-submit'),
    path('api/assessment/claim-latest/', views.ClaimLatestAssessmentView.as_view(), name='assessment-claim-latest')
]
