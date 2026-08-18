from django.contrib import admin
from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("public_id", "user", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("public_id", "user__email")
    inlines = (CartItemInline,)
