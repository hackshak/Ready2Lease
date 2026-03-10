import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import ListAPIView, RetrieveAPIView
from django.shortcuts import get_object_or_404

from .models import Blog
from .serializers import BlogListSerializer, BlogDetailSerializer
from .services.gemini_service import generate_blog
from .pagination import BlogPagination

from django.shortcuts import render, get_object_or_404
from .models import Blog
from django.core.paginator import Paginator




class BlogListAPI(ListAPIView):
    queryset = Blog.objects.filter(status="published").order_by("-created_at")
    serializer_class = BlogListSerializer
    pagination_class = BlogPagination




class BlogDetailAPI(APIView):

    def get(self, request, slug):

        blog = get_object_or_404(Blog, slug=slug, status="published")

        serializer = BlogDetailSerializer(blog)

        related_blogs = Blog.objects.filter(
            category=blog.category,
            status="published"
        ).exclude(id=blog.id)[:3]

        related_serializer = BlogListSerializer(related_blogs, many=True)

        return Response({
            "blog": serializer.data,
            "related_blogs": related_serializer.data
        })
    




class GenerateBlogAPI(APIView):

    def post(self, request):

        title = request.data.get("title")
        description = request.data.get("description")
        category = request.data.get("category")

        ai_response = generate_blog(title, description, category)

        data = json.loads(ai_response)

        return Response(data)
    



class ImproveBlogAPI(APIView):

    def post(self, request):

        content = request.data.get("content")

        improved_prompt = f"""
        Improve the following blog content.

        Requirements:
        - Improve SEO
        - Improve readability
        - Keep HTML formatting

        Content:
        {content}
        """

        from blog.services.gemini_service import genai

        model = genai.GenerativeModel("gemini-pro")

        response = model.generate_content(improved_prompt)

        return Response({
            "improved_content": response.text
        })
    








def blog_list(request):

    blogs = Blog.objects.filter(status="published").order_by("-created_at")

    paginator = Paginator(blogs, 5)

    page = request.GET.get("page")

    blogs = paginator.get_page(page)

    return render(request,"blog/blog_list.html",{"blogs":blogs})



def blog_detail(request, slug):

    blog = get_object_or_404(Blog, slug=slug, status="published")

    related_blogs = Blog.objects.filter(
        category=blog.category,
        status="published"
    ).exclude(id=blog.id)[:3]

    return render(request,"blog/blog_detail.html",{
        "blog":blog,
        "related_blogs":related_blogs
    })