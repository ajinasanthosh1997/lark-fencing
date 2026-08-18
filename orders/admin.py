from django.contrib import admin

from payments.models import Payment

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    readonly_fields = (
        "product",
        "product_name",
        "sku",
        "unit_price",
        "quantity",
        "line_total",
        "return_classification",
        "customization",
    )

    def has_add_permission(self, request, obj=None):
        return False


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    can_delete = False
    fields = (
        "public_id",
        "method",
        "provider",
        "status",
        "amount",
        "currency",
        "paid_at",
    )
    readonly_fields = ("public_id", "method", "provider", "amount", "currency")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "first_name",
        "last_name",
        "status",
        "payment_method",
        "total",
        "currency",
        "created_at",
    )
    list_filter = ("status", "payment_method", "fulfilment_method", "created_at")
    search_fields = ("order_number", "first_name", "last_name", "email", "phone")
    date_hierarchy = "created_at"
    readonly_fields = (
        "public_id",
        "order_number",
        "subtotal",
        "delivery_fee",
        "total",
        "currency",
        "returns_policy_version",
        "created_at",
        "updated_at",
    )
    inlines = (OrderItemInline, PaymentInline)

