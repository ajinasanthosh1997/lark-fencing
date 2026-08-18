from django.contrib import admin

from .models import Payment, Refund


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "method",
        "provider",
        "status",
        "amount",
        "currency",
        "created_at",
    )
    list_filter = ("method", "provider", "status", "created_at")
    search_fields = ("order__order_number", "provider_payment_id")
    readonly_fields = (
        "public_id",
        "order",
        "method",
        "amount",
        "currency",
        "created_at",
        "updated_at",
    )


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ("order", "amount", "status", "payment", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("order__order_number", "provider_refund_id")
    readonly_fields = (
        "public_id",
        "order",
        "payment",
        "return_request",
        "created_at",
    )
