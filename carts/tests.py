from decimal import Decimal

from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from catalog.models import Product, ProductVariant


class CartAPITests(APITestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name="Test Fence Panel",
            sku="TEST-001",
            price=Decimal("25.00"),
            stock_quantity=5,
        )

    def test_cart_crud_and_server_calculated_totals(self):
        response = self.client.post(reverse("cart-create"), {}, format="json")
        self.assertEqual(response.status_code, 201)
        cart_id = response.data["public_id"]

        response = self.client.post(
            reverse("cart-item-create", kwargs={"public_id": cart_id}),
            {"product_id": self.product.pk, "quantity": 2},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["item_count"], 2)
        self.assertEqual(response.data["subtotal"], "50.00")
        item_id = response.data["items"][0]["id"]

        response = self.client.patch(
            reverse("cart-item-detail", kwargs={"public_id": cart_id, "pk": item_id}),
            {"quantity": 3},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse("cart-detail", kwargs={"public_id": cart_id}))
        self.assertEqual(response.data["subtotal"], "75.00")

    def test_cart_rejects_quantity_above_stock(self):
        cart_id = self.client.post(reverse("cart-create"), {}, format="json").data["public_id"]
        response = self.client.post(
            reverse("cart-item-create", kwargs={"public_id": cart_id}),
            {"product_id": self.product.pk, "quantity": 6},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_cart_uses_selected_variant_price_and_stock(self):
        variant = ProductVariant.objects.create(product=self.product, name="1.8m × 1.8m", sku="TEST-001-L", price=Decimal("40.00"), stock_quantity=2)
        cart_id = self.client.post(reverse("cart-create"), {}, format="json").data["public_id"]
        response = self.client.post(reverse("cart-item-create", kwargs={"public_id": cart_id}), {"product_id": self.product.pk, "variant_id": variant.pk, "quantity": 2}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["subtotal"], "80.00")
        self.assertEqual(response.data["items"][0]["variant"]["name"], "1.8m × 1.8m")

    def test_add_to_cart_works_during_dashboard_session(self):
        staff = get_user_model().objects.create_user(username="cart-manager", password="test-password", is_staff=True)
        self.client.force_login(staff)
        cart_id = self.client.post(reverse("cart-create"), {}, format="json").data["public_id"]
        response = self.client.post(reverse("cart-item-create", kwargs={"public_id": cart_id}), {"product_id": self.product.pk, "quantity": 1}, format="json")
        self.assertEqual(response.status_code, 201)
