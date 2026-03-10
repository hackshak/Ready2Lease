from django.contrib import admin
from .models import Blog, Category
from .services.gemini_service import generate_blog


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):

    list_display = ("title", "category", "status", "created_at")

    def save_model(self, request, obj, form, change):

        # Generate AI blog only if content is empty
        if not obj.content:

            ai_data = generate_blog(
                obj.title,
                obj.short_description,
                obj.category.name
            )

            obj.content = ai_data.get("content", "")
            obj.meta_title = ai_data.get("meta_title", "")
            obj.meta_description = ai_data.get("meta_description", "")
            obj.meta_keywords = ai_data.get("meta_keywords", "")
            obj.slug = ai_data.get("slug", obj.slug)

        super().save_model(request, obj, form, change)