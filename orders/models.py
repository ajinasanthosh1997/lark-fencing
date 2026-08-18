import uuid

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from catalog.models import Product, ProductVariant


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING_PAYMENT = "pending_payment", "Pending payment"
        CONFIRMED = "confirmed", "Confirmed"
        PROCESSING = "processing", "Processing"
        READY = "ready", "Ready for collection / dispatch"
        DISPATCHED = "dispatched", "Dispatched"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"
        PARTIALLY_REFUNDED = "partially_refunded", "Partially refunded"
        REFUNDED = "refunded", "Refunded"

    class PaymentMethod(models.TextChoices):
        CASH_ON_DELIVERY = "cash_on_delivery", "Cash on delivery"
        PAYMENT_GATEWAY = "payment_gateway", "Payment gateway"

    class FulfilmentMethod(models.TextChoices):
        DELIVERY = "delivery", "Delivery"
        COLLECTION = "collection", "Collection"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    order_number = models.CharField(max_length=32, unique=True, editable=False)
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.PENDING_PAYMENT,
    )
    payment_method = models.CharField(max_length=30, choices=PaymentMethod.choices)
    fulfilment_method = models.CharField(
        max_length=20,
        choices=FulfilmentMethod.choices,
        default=FulfilmentMethod.DELIVERY,
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    address_line_1 = models.CharField(max_length=255, blank=True)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    county = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country_code = models.CharField(max_length=2, default="IE")
    customer_notes = models.TextField(blank=True, max_length=2000)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    delivery_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="EUR")
    returns_policy_version = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    dispatched_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    inventory_restocked_at = models.DateTimeField(null=True, blank=True, editable=False)
    staff_notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.order_number

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = (
                f"LF-{timezone.now():%Y%m%d}-{uuid.uuid4().hex[:8].upper()}"
            )
        self.email = self.email.lower()
        self.currency = self.currency.upper()
        self.country_code = self.country_code.upper()
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        related_name="order_items",
    )
    product_name = models.CharField(max_length=255)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True, related_name="order_items")
    variant_name = models.CharField(max_length=120, blank=True)
    sku = models.CharField(max_length=100)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    line_total = models.DecimalField(max_digits=12, decimal_places=2)
    return_classification = models.CharField(
        max_length=20,
        choices=Product.ReturnClassification.choices,
    )
    customization = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.quantity} × {self.product_name}"


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="status_history",
    )
    previous_status = models.CharField(
        max_length=30,
        choices=Order.Status.choices,
        blank=True,
    )
    new_status = models.CharField(max_length=30, choices=Order.Status.choices)
    note = models.TextField(blank=True, max_length=1000)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_status_changes",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-pk"]
        verbose_name_plural = "order status histories"

    def __str__(self):
        return f"{self.order.order_number}: {self.get_new_status_display()}"


class ReturnRequest(models.Model):
    class Reason(models.TextChoices):
        CHANGE_OF_MIND = "change_of_mind", "Change of mind"
        DAMAGED = "damaged", "Damaged goods"
        INCORRECT = "incorrect", "Incorrect goods"
        FAULTY = "faulty", "Faulty product"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        UNDER_REVIEW = "under_review", "Under review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        RECEIVED = "received", "Returned goods received"
        INSPECTED = "inspected", "Inspected"
        RESOLVED = "resolved", "Resolved"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    order = models.ForeignKey(
        Order,
        on_delete=models.PROTECT,
        related_name="return_requests",
    )
    reason = models.CharField(max_length=30, choices=Reason.choices)
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.REQUESTED,
    )
    contact_name = models.CharField(max_length=200)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=30, blank=True)
    description = models.TextField()
    customer_pays_return_shipping = models.BooleanField(default=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    received_at = models.DateTimeField(null=True, blank=True)
    inspected_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    staff_notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-requested_at"]

    def __str__(self):
        return f"{self.order.order_number} - {self.get_reason_display()}"


class ReturnItem(models.Model):
    class Resolution(models.TextChoices):
        REFUND = "refund", "Refund"
        REPLACEMENT = "replacement", "Replacement"
        REPAIR = "repair", "Repair"

    return_request = models.ForeignKey(
        ReturnRequest,
        on_delete=models.CASCADE,
        related_name="items",
    )
    order_item = models.ForeignKey(
        OrderItem,
        on_delete=models.PROTECT,
        related_name="return_items",
    )
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unused = models.BooleanField(default=False)
    uninstalled = models.BooleanField(default=False)
    original_packaging = models.BooleanField(default=False)
    clean_and_resalable = models.BooleanField(default=False)
    resolution = models.CharField(
        max_length=20,
        choices=Resolution.choices,
        default=Resolution.REFUND,
    )
    approved_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )


class ReturnEvidence(models.Model):
    return_request = models.ForeignKey(
        ReturnRequest,
        on_delete=models.CASCADE,
        related_name="evidence",
    )
    image = models.ImageField(upload_to="returns/%Y/%m/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
