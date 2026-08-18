from unittest.mock import patch
from decimal import Decimal

from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from catalog.models import Product, ProductVariant
from orders.models import Order, OrderItem
from payments.models import Payment

from .models import ContactEnquiry, CustomerReview, QuoteRequest, WebsiteContactSubmission


class WebsiteContactSubmissionApiTests(APITestCase):
    url = reverse("website-contact-create")

    def setUp(self):
        self.payload = {
            "first_name": " Jane ",
            "last_name": " Doe ",
            "email": "JANE@EXAMPLE.COM",
            "phone": "+1 555 0100",
            "message": "Please contact me about a fencing project.",
            "recaptcha_token": "browser-generated-token",
        }

    @patch("core.serializers.verify_recaptcha", return_value=True)
    def test_creates_contact_submission(self, verify_recaptcha):
        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(WebsiteContactSubmission.objects.count(), 1)
        submission = WebsiteContactSubmission.objects.get()
        self.assertEqual(submission.first_name, "Jane")
        self.assertEqual(submission.last_name, "Doe")
        self.assertEqual(submission.email, "jane@example.com")
        self.assertNotIn("recaptcha_token", response.data)
        verify_recaptcha.assert_called_once_with(
            "browser-generated-token", remote_ip="127.0.0.1"
        )

    @patch("core.serializers.verify_recaptcha", return_value=False)
    def test_rejects_invalid_recaptcha(self, verify_recaptcha):
        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("recaptcha_token", response.data)
        self.assertEqual(WebsiteContactSubmission.objects.count(), 0)


    def test_quote_and_contact_are_persisted(self):
        quote = self.client.post(reverse("quote-request-create"), {
            "first_name": "Jane", "last_name": "Doe", "email": "JANE@example.com", "address": "1 Main Street", "consent": True,
        }, format="json")
        contact = self.client.post(reverse("contact-enquiry-create"), {
            "name": "Jane Doe", "email": "jane@example.com", "message": "Please call me about fencing.", "consent": True,
        }, format="json")
        self.assertEqual((quote.status_code, contact.status_code), (201, 201))
        self.assertEqual((QuoteRequest.objects.count(), ContactEnquiry.objects.count()), (1, 1))

    def test_quote_consent_is_validated(self):
        quote = self.client.post(reverse("quote-request-create"), {
            "first_name": "Jane", "last_name": "Doe", "email": "jane@example.com", "address": "1 Main Street", "consent": False,
        }, format="json")
        self.assertEqual(quote.status_code, 400)

    def test_public_review_submission_is_disabled(self):
        response = self.client.post("/core/customer-reviews/", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_frontend_only_displays_approved_customer_reviews(self):
        CustomerReview.objects.create(
            reviewer="Approved Customer",
            project="Approved garden project",
            rating=4,
            review="This approved customer review should be visible.",
            permission=True,
            is_approved=True,
        )
        CustomerReview.objects.create(
            reviewer="Waiting Customer",
            project="Pending project",
            rating=5,
            review="This pending review must stay hidden.",
            permission=True,
            is_approved=False,
        )
        CustomerReview.objects.create(
            reviewer="No Permission",
            project="Private project",
            rating=5,
            review="This review has no display permission.",
            permission=False,
            is_approved=True,
        )

        for page_name in ("home", "about"):
            response = self.client.get(reverse(page_name))
            self.assertContains(response, "This approved customer review should be visible.")
            self.assertNotContains(response, "This pending review must stay hidden.")
            self.assertNotContains(response, "This review has no display permission.")
            self.assertNotContains(response, "Kildare homeowner")

    def test_home_hides_testimonial_section_without_approved_reviews(self):
        response = self.client.get(reverse("home"))
        self.assertNotContains(response, "Remembered for the finish")
        self.assertNotContains(response, "Write a review")

    @patch("core.serializers.verify_recaptcha", return_value=True)
    def test_validates_required_fields(self, verify_recaptcha):
        response = self.client.post(
            self.url,
            {"phone": "", "recaptcha_token": "browser-generated-token"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        for field in ("first_name", "last_name", "email"):
            self.assertIn(field, response.data)
        self.assertNotIn("phone", response.data)
        self.assertNotIn("message", response.data)
        self.assertEqual(WebsiteContactSubmission.objects.count(), 0)

    @patch("core.serializers.verify_recaptcha", return_value=True)
    def test_phone_and_message_are_optional(self, verify_recaptcha):
        response = self.client.post(
            self.url,
            {
                "first_name": "Jane",
                "last_name": "Doe",
                "email": "jane@example.com",
                "recaptcha_token": "browser-generated-token",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        submission = WebsiteContactSubmission.objects.get()
        self.assertEqual(submission.phone, "")
        self.assertEqual(submission.message, "")

    def test_get_is_not_allowed(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    @override_settings(RECAPTCHA_SECRET_KEY="")
    def test_returns_service_unavailable_when_recaptcha_is_not_configured(self):
        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(WebsiteContactSubmission.objects.count(), 0)


@override_settings(
    DEFAULT_DELIVERY_FEE="25.00",
    RETURNS_POLICY_VERSION="test-policy-v1",
)
class CommerceApiTests(APITestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name="Garden Fence Panel",
            sku="FENCE-001",
            price=Decimal("79.99"),
            stock_quantity=10,
        )
        self.order_payload = {
            "payment_method": Order.PaymentMethod.CASH_ON_DELIVERY,
            "fulfilment_method": Order.FulfilmentMethod.DELIVERY,
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "JANE@EXAMPLE.COM",
            "phone": "0890000000",
            "address_line_1": "1 Main Street",
            "city": "Dublin",
            "county": "Dublin",
            "country_code": "ie",
            "items": [{"product_id": self.product.pk, "quantity": 2}],
        }

    def test_product_catalog_only_returns_active_products(self):
        Product.objects.create(
            name="Hidden product",
            sku="HIDDEN-001",
            price=Decimal("10.00"),
            is_active=False,
        )

        response = self.client.get(reverse("product-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["sku"], "FENCE-001")

    def test_cod_order_uses_server_prices_and_reserves_inventory(self):
        self.order_payload.update(
            {
                "subtotal": "0.01",
                "delivery_fee": "0.00",
                "total": "0.01",
                "status": Order.Status.REFUNDED,
            }
        )

        response = self.client.post(
            reverse("order-create"),
            self.order_payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        order = Order.objects.get()
        self.product.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CONFIRMED)
        self.assertEqual(order.subtotal, Decimal("159.98"))
        self.assertEqual(order.delivery_fee, Decimal("25.00"))
        self.assertEqual(order.total, Decimal("184.98"))
        self.assertEqual(order.email, "jane@example.com")
        self.assertEqual(order.returns_policy_version, "test-policy-v1")
        self.assertEqual(self.product.stock_quantity, 8)
        payment = Payment.objects.get(order=order)
        self.assertEqual(payment.method, Order.PaymentMethod.CASH_ON_DELIVERY)
        self.assertEqual(payment.status, Payment.Status.PENDING)
        self.assertEqual(payment.amount, order.total)

    def test_gateway_order_cannot_be_marked_paid_by_frontend(self):
        self.order_payload.update(
            {
                "payment_method": Order.PaymentMethod.PAYMENT_GATEWAY,
                "gateway_provider": "stripe",
            }
        )

        response = self.client.post(
            reverse("order-create"),
            self.order_payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        order = Order.objects.get()
        payment = Payment.objects.get(order=order)
        self.assertEqual(order.status, Order.Status.PENDING_PAYMENT)
        self.assertEqual(payment.status, Payment.Status.INITIATED)
        self.assertEqual(payment.provider, "stripe")
        self.assertIsNone(payment.provider_payment_id)

    def test_gateway_provider_is_required_for_gateway_payment(self):
        self.order_payload["payment_method"] = Order.PaymentMethod.PAYMENT_GATEWAY

        response = self.client.post(
            reverse("order-create"),
            self.order_payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("gateway_provider", response.data)
        self.assertFalse(Order.objects.exists())

    def test_insufficient_stock_does_not_create_partial_order(self):
        self.order_payload["items"][0]["quantity"] = 11

        response = self.client.post(
            reverse("order-create"),
            self.order_payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Order.objects.exists())
        self.assertFalse(Payment.objects.exists())
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 10)

    def test_order_uses_variant_price_sku_and_inventory(self):
        variant = ProductVariant.objects.create(product=self.product, name="Large", sku="FENCE-001-L", price=Decimal("99.00"), stock_quantity=3)
        self.order_payload["items"] = [{"product_id": self.product.pk, "variant_id": variant.pk, "quantity": 2}]
        response = self.client.post(reverse("order-create"), self.order_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        item = OrderItem.objects.get()
        variant.refresh_from_db()
        self.assertEqual(item.variant_name, "Large")
        self.assertEqual(item.sku, "FENCE-001-L")
        self.assertEqual(item.unit_price, Decimal("99.00"))
        self.assertEqual(variant.stock_quantity, 1)

    def test_return_api_is_not_exposed(self):
        response = self.client.post("/api/v1/returns/", {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_checkout_is_cash_on_delivery_only(self):
        response = self.client.get(reverse("checkout"))

        self.assertContains(response, "Cash on delivery")
        self.assertContains(response, "Place cash-on-delivery order")
        self.assertNotContains(response, "Card number")
        self.assertNotContains(response, "Returns &amp; refunds")

    def test_old_returns_page_redirects_to_current_policy(self):
        response = self.client.get("/returns/")

        self.assertRedirects(
            response,
            reverse("policy-detail", args=["cancellation-and-returns"]),
            fetch_redirect_response=False,
        )

    def test_policy_pages_and_checkout_policy_links_are_public(self):
        for slug in (
            "terms-and-conditions",
            "privacy-policy",
            "delivery-and-collection",
            "cancellation-and-returns",
            "cookie-policy",
        ):
            response = self.client.get(reverse("policy-detail", args=[slug]))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "Formal legal review pending")

        checkout = self.client.get(reverse("checkout"))
        self.assertContains(checkout, reverse("policy-detail", args=["terms-and-conditions"]))
        self.assertContains(checkout, reverse("policy-detail", args=["privacy-policy"]))
        self.assertContains(checkout, reverse("policy-detail", args=["delivery-and-collection"]))
        self.assertContains(checkout, reverse("policy-detail", args=["cancellation-and-returns"]))
