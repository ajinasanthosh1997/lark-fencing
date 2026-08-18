from django.contrib import admin

from core.models import GalleryItem

from .models import Product


class ProductGalleryInline(admin.TabularInline):
    model = GalleryItem
    extra = 1
    fields = ("title", "image", "category")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "sku",
        "category",
        "price",
        "currency",
        "stock_quantity",
        "is_active",
    )
    list_filter = ("is_active", "category")
    search_fields = ("name", "sku", "description")
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ("category",)
    inlines = (ProductGalleryInline,)
    fieldsets = (
        ("Product", {"fields": ("name", "slug", "sku", "description", "category", "image_name")}),
        ("Price and stock", {"fields": ("price", "currency", "track_inventory", "stock_quantity")}),
        ("Availability", {"fields": ("is_active",)}),
    )
