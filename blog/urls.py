from django.urls import path
from .views import (
    BlogListAPI,
    BlogDetailAPI,
    GenerateBlogAPI,
    ImproveBlogAPI,
    blog_list,
    blog_detail
)



urlpatterns = [

    # WEBSITE PAGES
    path("blogs/", blog_list, name="blog_list"),
    path("blogs/<slug:slug>/", blog_detail, name="blog_detail"),


    # API ENDPOINTS
    path("api/blogs/", BlogListAPI.as_view()),
    path("api/blogs/<slug:slug>/", BlogDetailAPI.as_view()),
    path("api/blogs/generate/", GenerateBlogAPI.as_view()),
    path("api/blogs/improve/", ImproveBlogAPI.as_view()),

]