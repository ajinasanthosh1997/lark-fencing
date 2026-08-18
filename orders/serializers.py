from collections import defaultdict
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from rest_framework import serializers

from catalog.models import Product, ProductVariant
from payments.models import Payment

from .models import Order, OrderItem, OrderStatusHistory, ReturnEvidence, ReturnItem, ReturnRequest


class OrderItemInputSerializer(serializers.Serializer):
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_active=True),
        source="product",
    )
    quantity = serializers.IntegerField(min_value=1, max_value=1000)
    variant_id = serializers.PrimaryKeyRelatedField(queryset=ProductVariant.objects.filter(is_active=True), source="variant", required=False, allow_null=True)
    customization = serializers.JSONField(required=False, default=dict)


class OrderItemSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = OrderItem
        fields = (
            "id",
            "product_id",
            "product_name",
            "variant_id",
            "variant_name",
            "sku",
            "unit_price",
            "quantity",
            "line_total",
            "return_classification",
            "customization",
        )
        read_only_fields = fields


class PaymentSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = (
            "public_id",
            "method",
            "provider",
            "status",
            "amount",
            "currency",
        )
        read_only_fields = fields


class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemInputSerializer(many=True, write_only=True)
    gateway_provider = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
        write_only=True,
    )
    order_items = OrderItemSerializer(source="items", many=True, read_only=True)
    payments = PaymentSummarySerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = (
            "public_id",
            "order_number",
            "status",
            "payment_method",
            "fulfilment_method",
            "first_name",
            "last_name",
            "email",
            "phone",
            "address_line_1",
            "address_line_2",
            "city",
            "county",
            "postal_code",
            "country_code",
            "customer_notes",
            "items",
            "gateway_provider",
            "order_items",
            "payments",
            "subtotal",
            "delivery_fee",
            "total",
            "currency",
            "returns_policy_version",
            "created_at",
        )
        read_only_fields = (
            "public_id",
            "order_number",
            "status",
            "order_items",
            "payments",
            "subtotal",
            "delivery_fee",
            "total",
            "currency",
            "returns_policy_version",
            "created_at",
        )
        extra_kwargs = {
            "email": {"trim_whitespace": True},
            "country_code": {"required": False},
            "customer_notes": {"required": False, "allow_blank": True},
        }

    def validate(self, attrs):
        items = attrs.get("items", [])
        if not items:
            raise serializers.ValidationError({"items": "Add at least one product."})

        attrs.setdefault("fulfilment_method", Order.FulfilmentMethod.DELIVERY)
        if (
            attrs["payment_method"] == Order.PaymentMethod.PAYMENT_GATEWAY
            and not attrs.get("gateway_provider")
        ):
            raise serializers.ValidationError(
                {"gateway_provider": "This field is required for gateway payments."}
            )
        if (
            attrs["payment_method"] == Order.PaymentMethod.CASH_ON_DELIVERY
            and attrs.get("gateway_provider")
        ):
            raise serializers.ValidationError(
                {"gateway_provider": "Do not provide a gateway for cash on delivery."}
            )

        if attrs["fulfilment_method"] == Order.FulfilmentMethod.DELIVERY:
            required_address_fields = ("address_line_1", "city", "county")
            missing = [field for field in required_address_fields if not attrs.get(field)]
            if missing:
                raise serializers.ValidationError(
                    {field: "This field is required for delivery." for field in missing}
                )

        currencies = {item["product"].currency for item in items}
        if len(currencies) != 1:
            raise serializers.ValidationError(
                {"items": "All products in an order must use the same currency."}
            )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        submitted_items = validated_data.pop("items")
        gateway_provider = validated_data.pop("gateway_provider", "")

        requested_quantities = defaultdict(int)
        customizations = defaultdict(list)
        for item in submitted_items:
            product_id = item["product"].pk
            variant = item.get("variant")
            if variant and variant.product_id != product_id:
                raise serializers.ValidationError({"items": "A selected variant does not belong to its product."})
            key = (product_id, variant.pk if variant else None)
            requested_quantities[key] += item["quantity"]
            customizations[key].append(item.get("customization", {}))

        products = {
            product.pk: product
            for product in Product.objects.select_for_update().filter(
                pk__in={key[0] for key in requested_quantities},
                is_active=True,
            )
        }
        if len(products) != len({key[0] for key in requested_quantities}):
            raise serializers.ValidationError(
                {"items": "One or more products are no longer available."}
            )

        subtotal = Decimal("0.00")
        item_rows = []
        variant_ids = {key[1] for key in requested_quantities if key[1]}
        variants = {variant.pk: variant for variant in ProductVariant.objects.select_for_update().filter(pk__in=variant_ids, is_active=True)}
        if len(variants) != len(variant_ids):
            raise serializers.ValidationError({"items": "One or more variants are no longer available."})
        for key, quantity in requested_quantities.items():
            product_id, variant_id = key
            product = products[product_id]
            variant = variants.get(variant_id)
            available = variant.stock_quantity if variant else product.stock_quantity
            if product.track_inventory and available < quantity:
                raise serializers.ValidationError(
                    {
                        "items": (
                            f"Only {available} unit(s) of "
                            f"{product.name} are available."
                        )
                    }
                )
            unit_price = variant.price if variant else product.price
            line_total = unit_price * quantity
            subtotal += line_total
            item_rows.append((product, variant, quantity, unit_price, line_total, key))

        delivery_fee = (
            Decimal(str(settings.DEFAULT_DELIVERY_FEE))
            if validated_data["fulfilment_method"] == Order.FulfilmentMethod.DELIVERY
            else Decimal("0.00")
        )
        currency = next(iter(products.values())).currency
        is_cod = (
            validated_data["payment_method"] == Order.PaymentMethod.CASH_ON_DELIVERY
        )
        order = Order.objects.create(
            **validated_data,
            status=Order.Status.CONFIRMED if is_cod else Order.Status.PENDING_PAYMENT,
            confirmed_at=timezone.now() if is_cod else None,
            subtotal=subtotal,
            delivery_fee=delivery_fee,
            total=subtotal + delivery_fee,
            currency=currency,
            returns_policy_version=settings.RETURNS_POLICY_VERSION,
        )

        for product, variant, quantity, unit_price, line_total, key in item_rows:
            OrderItem.objects.create(
                order=order,
                product=product,
                product_name=product.name,
                variant=variant,
                variant_name=variant.name if variant else "",
                sku=variant.sku if variant else product.sku,
                unit_price=unit_price,
                quantity=quantity,
                line_total=line_total,
                return_classification=product.return_classification,
                customization={"entries": customizations[key]},
            )
            if product.track_inventory:
                if variant:
                    variant.stock_quantity -= quantity
                    variant.save(update_fields=["stock_quantity"])
                else:
                    product.stock_quantity -= quantity
                    product.save(update_fields=["stock_quantity", "updated_at"])

        Payment.objects.create(
            order=order,
            method=order.payment_method,
            provider=gateway_provider,
            status=Payment.Status.PENDING if is_cod else Payment.Status.INITIATED,
            amount=order.total,
            currency=order.currency,
        )
        OrderStatusHistory.objects.create(
            order=order,
            new_status=order.status,
            note="Order placed through the storefront.",
        )
        return order


class ReturnItemInputSerializer(serializers.Serializer):
    order_item_id = serializers.PrimaryKeyRelatedField(
        queryset=OrderItem.objects.all(),
        source="order_item",
    )
    quantity = serializers.IntegerField(min_value=1)
    unused = serializers.BooleanField(default=False)
    uninstalled = serializers.BooleanField(default=False)
    original_packaging = serializers.BooleanField(default=False)
    clean_and_resalable = serializers.BooleanField(default=False)
    resolution = serializers.ChoiceField(
        choices=ReturnItem.Resolution.choices,
        default=ReturnItem.Resolution.REFUND,
    )


class ReturnRequestCreateSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(write_only=True)
    order_email = serializers.EmailField(write_only=True)
    items = ReturnItemInputSerializer(many=True, write_only=True)

    class Meta:
        model = ReturnRequest
        fields = (
            "public_id",
            "order_number",
            "order_email",
            "reason",
            "status",
            "contact_name",
            "contact_email",
            "contact_phone",
            "description",
            "items",
            "customer_pays_return_shipping",
            "requested_at",
        )
        read_only_fields = (
            "public_id",
            "status",
            "customer_pays_return_shipping",
            "requested_at",
        )

    def validate(self, attrs):
        order_number = attrs.pop("order_number")
        order_email = attrs.pop("order_email").lower()
        try:
            order = Order.objects.get(
                order_number__iexact=order_number,
                email__iexact=order_email,
            )
        except Order.DoesNotExist as exc:
            raise serializers.ValidationError(
                {"order_number": "Order details could not be verified."}
            ) from exc

        if not order.delivered_at:
            raise serializers.ValidationError(
                {"order_number": "A return can only be requested after delivery."}
            )

        elapsed = timezone.now() - order.delivered_at
        reason = attrs["reason"]
        if reason == ReturnRequest.Reason.CHANGE_OF_MIND and elapsed.days >= 14:
            raise serializers.ValidationError(
                {"reason": "The 14-day change-of-mind return period has expired."}
            )
        if reason in (
            ReturnRequest.Reason.DAMAGED,
            ReturnRequest.Reason.INCORRECT,
        ) and elapsed.total_seconds() > 48 * 60 * 60:
            raise serializers.ValidationError(
                {"reason": "Damaged or incorrect goods must be reported within 48 hours."}
            )

        submitted_items = attrs.get("items", [])
        if not submitted_items:
            raise serializers.ValidationError({"items": "Add at least one order item."})
        submitted_quantities = defaultdict(int)
        for item in submitted_items:
            order_item = item["order_item"]
            if order_item.order_id != order.pk:
                raise serializers.ValidationError(
                    {"items": "Every item must belong to the specified order."}
                )
            submitted_quantities[order_item.pk] += item["quantity"]
            already_requested = (
                ReturnItem.objects.filter(order_item=order_item)
                .exclude(return_request__status=ReturnRequest.Status.REJECTED)
                .aggregate(total=Sum("quantity"))["total"]
                or 0
            )
            if submitted_quantities[order_item.pk] + already_requested > order_item.quantity:
                raise serializers.ValidationError(
                    {
                        "items": (
                            f"Return quantity exceeds the order quantity for "
                            f"{order_item.sku}."
                        )
                    }
                )
            if reason == ReturnRequest.Reason.CHANGE_OF_MIND:
                if (
                    order_item.return_classification
                    != Product.ReturnClassification.STANDARD
                ):
                    raise serializers.ValidationError(
                        {
                            "items": (
                                f"{order_item.product_name} is not returnable "
                                "for change of mind."
                            )
                        }
                    )
                required_conditions = (
                    item["unused"],
                    item["uninstalled"],
                    item["original_packaging"],
                    item["clean_and_resalable"],
                )
                if not all(required_conditions):
                    raise serializers.ValidationError(
                        {"items": "Change-of-mind items must meet all return conditions."}
                    )

        attrs["order"] = order
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        items = validated_data.pop("items")
        reason = validated_data["reason"]
        return_request = ReturnRequest.objects.create(
            **validated_data,
            customer_pays_return_shipping=reason
            not in (
                ReturnRequest.Reason.DAMAGED,
                ReturnRequest.Reason.INCORRECT,
                ReturnRequest.Reason.FAULTY,
            ),
        )
        for item in items:
            ReturnItem.objects.create(return_request=return_request, **item)
        return return_request


class ReturnEvidenceCreateSerializer(serializers.ModelSerializer):
    return_request_id = serializers.UUIDField(write_only=True)
    order_email = serializers.EmailField(write_only=True)

    class Meta:
        model = ReturnEvidence
        fields = (
            "id",
            "return_request_id",
            "order_email",
            "image",
            "uploaded_at",
        )
        read_only_fields = ("id", "uploaded_at")

    def validate(self, attrs):
        return_request_id = attrs.pop("return_request_id")
        order_email = attrs.pop("order_email")
        try:
            return_request = ReturnRequest.objects.select_related("order").get(
                public_id=return_request_id,
                order__email__iexact=order_email,
            )
        except ReturnRequest.DoesNotExist as exc:
            raise serializers.ValidationError(
                {"return_request_id": "Return request details could not be verified."}
            ) from exc
        attrs["return_request"] = return_request
        return attrs
