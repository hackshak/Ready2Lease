# blog/serializers.py

from rest_framework import serializers
from .models import Blog, Category


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = "__all__"


class BlogListSerializer(serializers.ModelSerializer):

    category = CategorySerializer()

    class Meta:
        model = Blog
        fields = [
            "id",
            "title",
            "slug",
            "short_description",
            "image",
            "category",
            "created_at"
        ]


class BlogDetailSerializer(serializers.ModelSerializer):

    category = CategorySerializer()

    class Meta:
        model = Blog
        fields = "__all__"