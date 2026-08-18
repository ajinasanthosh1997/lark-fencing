from decimal import Decimal

from rest_framework import serializers

from catalog.models import Product, ProductVariant
from catalog.serializers import ProductSerializer, ProductVariantSerializer
from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter(is_active=True), source="product", write_only=True)
    line_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    variant = ProductVariantSerializer(read_only=True)
    variant_id = serializers.PrimaryKeyRelatedField(queryset=ProductVariant.objects.filter(is_active=True), source="variant", write_only=True, required=False, allow_null=True)

    class Meta:
        model = CartItem
        fields = ("id", "product", "product_id", "variant", "variant_id", "quantity", "customization", "line_total")
        extra_kwargs = {"product_id": {"required": False}}

    def validate(self, attrs):
        product = attrs.get("product") or getattr(self.instance, "product", None)
        quantity = attrs.get("quantity", getattr(self.instance, "quantity", 1))
        variant = attrs.get("variant", getattr(self.instance, "variant", None))
        if not self.instance and not product:
            raise serializers.ValidationError({"product_id": "This field is required."})
        if variant and product and variant.product_id != product.pk:
            raise serializers.ValidationError({"variant_id": "This variant does not belong to the selected product."})
        available = variant.stock_quantity if variant else (product.stock_quantity if product else 0)
        if product and product.track_inventory and quantity > available:
            raise serializers.ValidationError({"quantity": f"Only {available} unit(s) are available."})
        return attrs


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    item_count = serializers.SerializerMethodField()
    subtotal = serializers.SerializerMethodField()
    currency = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ("public_id", "is_active", "items", "item_count", "subtotal", "currency", "created_at", "updated_at")
        read_only_fields = fields

    def get_item_count(self, obj):
        return sum(item.quantity for item in obj.items.all())

    def get_subtotal(self, obj):
        total = sum((item.line_total for item in obj.items.all()), Decimal("0.00"))
        return f"{total:.2f}"

    def get_currency(self, obj):
        currencies = {item.product.currency for item in obj.items.all()}
        return next(iter(currencies), "EUR") if len(currencies) <= 1 else "MIXED"
