from django.contrib import admin

from .models import PageSEO


@admin.register(PageSEO)
class PageSEOAdmin(admin.ModelAdmin):
    list_display = ("url_path", "title", "robots", "updated_at")
    search_fields = ("url_path", "title", "meta_description", "meta_keywords", "h1_tag")
    list_filter = ("robots",)
