from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.test import TestCase

from catalog.models import Product, ProductCalculatorProfile, ProjectCalculatorSettings, SmartFenceCalculatorRate, SmartFenceCalculatorSettings
from orders.models import Order, OrderItem, OrderStatusHistory
from payments.models import Payment

from .dashboard_forms import LegalPolicyForm
from .models import Banner, Category, CustomerReview, GalleryItem, LegalPolicy, QuoteRequest, SubmissionFollowUp, WebsiteSettings


GIF = b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"


class DashboardTests(TestCase):
    def setUp(self):
        self.staff = get_user_model().objects.create_user(username="manager", email="manager@example.com", password="test-password", is_staff=True, is_superuser=True)

    def create_dashboard_order(self):
        product = Product.objects.create(
            name="Workflow Fence Panel",
            sku="WORKFLOW-001",
            image_name="solid-cottage.png",
            price="50.00",
            stock_quantity=7,
            track_inventory=True,
        )
        order = Order.objects.create(
            status=Order.Status.CONFIRMED,
            payment_method=Order.PaymentMethod.CASH_ON_DELIVERY,
            fulfilment_method=Order.FulfilmentMethod.DELIVERY,
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com",
            phone="0890000000",
            address_line_1="1 Main Street",
            city="Dublin",
            county="Dublin",
            postal_code="D12 E398",
            customer_notes="Call before delivery.",
            subtotal="100.00",
            delivery_fee="10.00",
            total="110.00",
            currency="EUR",
            returns_policy_version="historical",
        )
        OrderItem.objects.create(
            order=order,
            product=product,
            product_name=product.name,
            sku=product.sku,
            unit_price="50.00",
            quantity=2,
            line_total="100.00",
            return_classification=Product.ReturnClassification.STANDARD,
        )
        payment = Payment.objects.create(
            order=order,
            method=Order.PaymentMethod.CASH_ON_DELIVERY,
            status=Payment.Status.PENDING,
            amount="110.00",
            currency="EUR",
        )
        return order, product, payment

    def test_dashboard_requires_staff_and_renders_sections(self):
        response = self.client.get(reverse("dashboard-home"))
        self.assertRedirects(response, f"{reverse('dashboard-login')}?next={reverse('dashboard-home')}")
        self.client.force_login(self.staff)
        response = self.client.get(reverse("dashboard-home"))
        self.assertContains(response, "Website dashboard")
        self.assertContains(response, "Banners")
        self.assertContains(response, 'data-nav-group="products"')
        self.assertContains(response, "Product management")
        self.assertContains(response, "Product variants")
        self.assertContains(response, "Legal policies")
        self.assertContains(response, "SEO content")
        self.assertNotContains(response, ">Returns<")
        self.assertEqual(
            self.client.get(reverse("dashboard-list", args=["returns"])).status_code,
            404,
        )

    def test_dashboard_created_review_is_publishable_without_permission_field(self):
        self.client.force_login(self.staff)
        response = self.client.post(reverse("dashboard-create", args=["reviews"]), {
            "reviewer": "Dublin Customer",
            "project": "Supply and professional fitting",
            "rating": 5,
            "review": "Excellent fitting and a tidy finish.",
            "is_approved": "on",
        })
        self.assertEqual(response.status_code, 302)
        review = CustomerReview.objects.get(reviewer="Dublin Customer")
        self.assertTrue(review.permission)
        self.assertTrue(review.is_approved)

    def test_ordinary_staff_cannot_access_dashboard(self):
        ordinary_staff = get_user_model().objects.create_user(username="staff", password="test-password", is_staff=True)
        self.client.force_login(ordinary_staff)
        response = self.client.get(reverse("dashboard-home"))
        self.assertRedirects(response, f"{reverse('dashboard-login')}?next={reverse('dashboard-home')}")

    def test_legal_policy_requires_reviewer_details_before_approval(self):
        policy = LegalPolicy.objects.get(slug="terms-and-conditions")
        data = {
            "title": policy.title,
            "slug": policy.slug,
            "summary": policy.summary,
            "body": policy.body,
            "version": "1.0",
            "effective_date": "2026-08-18",
            "review_status": LegalPolicy.ReviewStatus.APPROVED,
            "reviewed_by": "",
            "reviewed_at": "",
            "display_order": policy.display_order,
            "is_active": "on",
        }
        form = LegalPolicyForm(data=data, instance=policy)

        self.assertFalse(form.is_valid())
        self.assertIn("reviewed_by", form.errors)
        self.assertIn("reviewed_at", form.errors)

    def test_cash_on_delivery_payment_opens_the_complete_order_workflow(self):
        order = Order.objects.create(
            payment_method=Order.PaymentMethod.CASH_ON_DELIVERY,
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com",
            phone="0890000000",
            subtotal="60.00",
            total="60.00",
            returns_policy_version="historical",
        )
        payment = Payment.objects.create(
            order=order,
            method=Order.PaymentMethod.CASH_ON_DELIVERY,
            status=Payment.Status.PENDING,
            amount="60.00",
            currency="EUR",
        )
        self.client.force_login(self.staff)

        response = self.client.get(reverse("dashboard-edit", args=["payments", payment.pk]))
        order_url = reverse("dashboard-edit", args=["orders", order.pk])
        self.assertRedirects(response, order_url)
        page = self.client.get(order_url)
        self.assertContains(page, "Cash on delivery")
        self.assertContains(page, "Amount due")
        self.assertContains(page, "Mark cash collected")
        self.assertNotContains(page, "Provider payment id")
        self.assertNotContains(page, "Provider metadata")
        self.assertNotContains(page, "Failure reason")

    def test_order_detail_shows_products_customer_totals_and_notes(self):
        order, _, _ = self.create_dashboard_order()
        self.client.force_login(self.staff)

        page = self.client.get(reverse("dashboard-edit", args=["orders", order.pk]))

        self.assertContains(page, order.order_number)
        self.assertContains(page, "Workflow Fence Panel")
        self.assertContains(page, "SKU WORKFLOW-001")
        self.assertContains(page, "EUR 110.00")
        self.assertContains(page, "1 Main Street")
        self.assertContains(page, "Call before delivery.")
        self.assertContains(page, "Cash on delivery")
        self.assertContains(page, "Print order")
        self.assertContains(page, 'aria-label="Complete order workflow"')
        self.assertContains(page, "Ready")
        self.assertContains(page, "Dispatched")
        self.assertContains(page, "Delivered")
        self.assertContains(page, "only shows valid next steps")
        self.assertNotContains(page, "Delete")

        response = self.client.post(
            reverse("dashboard-edit", args=["orders", order.pk]),
            {"action": "save_notes", "staff_notes": "Customer confirmed side access."},
        )
        self.assertRedirects(response, reverse("dashboard-edit", args=["orders", order.pk]))
        order.refresh_from_db()
        self.assertEqual(order.staff_notes, "Customer confirmed side access.")

        response = self.client.post(
            reverse("dashboard-edit", args=["orders", order.pk]),
            {
                "action": "save_delivery",
                "first_name": "Jane",
                "last_name": "Doe",
                "email": "jane@example.com",
                "phone": "0890000000",
                "fulfilment_method": Order.FulfilmentMethod.DELIVERY,
                "address_line_1": "2 Updated Street",
                "address_line_2": "",
                "city": "Dublin",
                "county": "Dublin",
                "postal_code": "D12 E398",
                "country_code": "IE",
                "customer_notes": "Use the side gate.",
            },
        )
        self.assertRedirects(response, reverse("dashboard-edit", args=["orders", order.pk]))
        order.refresh_from_db()
        self.assertEqual(order.address_line_1, "2 Updated Street")
        self.assertEqual(order.customer_notes, "Use the side gate.")

    def test_order_status_actions_are_audited_and_cancellation_restocks_once(self):
        order, product, payment = self.create_dashboard_order()
        self.client.force_login(self.staff)
        url = reverse("dashboard-edit", args=["orders", order.pk])

        self.client.post(url, {"action": "change_status", "next_status": Order.Status.PROCESSING, "status_note": "Order checked by phone."})
        order.refresh_from_db()
        history = OrderStatusHistory.objects.get(order=order)
        self.assertEqual(order.status, Order.Status.PROCESSING)
        self.assertEqual(history.previous_status, Order.Status.CONFIRMED)
        self.assertEqual(history.new_status, Order.Status.PROCESSING)
        self.assertEqual(history.changed_by, self.staff)
        self.assertEqual(history.note, "Order checked by phone.")

        self.client.post(url, {"action": "change_status", "next_status": Order.Status.CANCELLED, "status_note": "Customer cancelled before dispatch."})
        order.refresh_from_db(); product.refresh_from_db(); payment.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CANCELLED)
        self.assertIsNotNone(order.inventory_restocked_at)
        self.assertEqual(product.stock_quantity, 9)
        self.assertEqual(payment.status, Payment.Status.CANCELLED)

        self.client.post(url, {"action": "change_status", "next_status": Order.Status.CANCELLED})
        product.refresh_from_db()
        self.assertEqual(product.stock_quantity, 9)

    def test_staff_can_record_cash_collection_and_financial_records_cannot_be_deleted(self):
        order, _, payment = self.create_dashboard_order()
        self.client.force_login(self.staff)

        response = self.client.post(
            reverse("dashboard-edit", args=["orders", order.pk]),
            {"action": "mark_cash_paid"},
        )
        self.assertRedirects(response, reverse("dashboard-edit", args=["orders", order.pk]))
        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.PAID)
        self.assertIsNotNone(payment.paid_at)
        self.assertEqual(self.client.get(reverse("dashboard-delete", args=["orders", order.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("dashboard-delete", args=["payments", payment.pk])).status_code, 404)

    def test_product_create_edit_and_delete(self):
        self.client.force_login(self.staff)
        create_page = self.client.get(reverse("dashboard-create", args=["products"]))
        self.assertNotContains(create_page, "Return classification")
        self.assertContains(create_page, "completed orders reduce the stock quantity")
        self.assertContains(create_page, "This limit is enforced only when Track inventory is enabled")
        payload = {"name": "Dashboard Fence", "sku": "DASH-001", "price": "50.00", "currency": "EUR", "stock_quantity": 4, "track_inventory": "on", "is_active": "on"}
        response = self.client.post(reverse("dashboard-create", args=["products"]), payload)
        self.assertRedirects(response, reverse("dashboard-list", args=["products"]))
        product = Product.objects.get(sku="DASH-001")
        self.assertEqual(product.return_classification, Product.ReturnClassification.STANDARD)
        payload.update({"name": "Updated Fence", "price": "55.00"})
        self.client.post(reverse("dashboard-edit", args=["products", product.pk]), payload)
        product.refresh_from_db(); self.assertEqual(product.name, "Updated Fence")
        self.client.post(reverse("dashboard-delete", args=["products", product.pk]))
        self.assertFalse(Product.objects.filter(pk=product.pk).exists())

    def test_product_and_variants_can_be_created_together(self):
        self.client.force_login(self.staff)
        create_page = self.client.get(reverse("dashboard-create", args=["products"]))
        self.assertContains(create_page, "Product variants")
        self.assertContains(create_page, "+ Add variant")
        self.assertContains(create_page, "Enable to show and sell this product")
        response = self.client.post(reverse("dashboard-create", args=["products"]), {
            "name": "Panel With Options",
            "sku": "PANEL-OPTIONS",
            "description": "A panel with two sizes.",
            "image_name": "solid-cottage.png",
            "price": "40.00",
            "currency": "EUR",
            "track_inventory": "on",
            "stock_quantity": "12",
            "is_active": "on",
            "variants-TOTAL_FORMS": "2",
            "variants-INITIAL_FORMS": "0",
            "variants-MIN_NUM_FORMS": "0",
            "variants-MAX_NUM_FORMS": "1000",
            "variants-0-size": "1.8m × 1.8m",
            "variants-0-style": "Pressure Treated",
            "variants-0-sku": "PANEL-OPTIONS-1818",
            "variants-0-price": "55.00",
            "variants-0-stock_quantity": "8",
            "variants-0-display_order": "1",
            "variants-0-is_active": "on",
            "variants-1-size": "1.8m × 1.5m",
            "variants-1-style": "Pressure Treated",
            "variants-1-sku": "PANEL-OPTIONS-1815",
            "variants-1-price": "49.00",
            "variants-1-stock_quantity": "4",
            "variants-1-display_order": "2",
            "variants-1-is_active": "on",
        })
        self.assertRedirects(response, reverse("dashboard-list", args=["products"]))
        product = Product.objects.get(sku="PANEL-OPTIONS")
        self.assertEqual(product.variants.count(), 2)
        self.assertTrue(product.variants.filter(sku="PANEL-OPTIONS-1818", price="55.00", is_active=True).exists())

    def test_dashboard_lists_are_paginated_and_filterable(self):
        Product.objects.bulk_create([
            Product(name=f"Fence {index}", slug=f"page-fence-{index}", sku=f"PAGE-{index:03}", price="10.00", is_active=index % 2 == 0)
            for index in range(25)
        ])
        self.client.force_login(self.staff)
        response = self.client.get(reverse("dashboard-list", args=["products"]), {"per_page": 10, "active": "true"})
        self.assertEqual(len(response.context["rows"]), 10)
        self.assertEqual(response.context["page_obj"].paginator.count, 13)
        self.assertContains(response, "Page 1 of 2")

    def test_dynamic_banner_and_gallery_render_publicly(self):
        category = Category.objects.create(name="Garden")
        Banner.objects.create(title="Managed banner", image=SimpleUploadedFile("banner.gif", GIF, content_type="image/gif"), image_alt="Managed garden")
        GalleryItem.objects.create(title="Managed gallery", category=category, image=SimpleUploadedFile("gallery.gif", GIF, content_type="image/gif"), display_size="wide")
        self.assertContains(self.client.get(reverse("home")), "Managed banner")
        gallery = self.client.get(reverse("gallery"))
        self.assertContains(gallery, "Managed gallery")
        self.assertContains(gallery, 'data-gallery-filter="%s"' % category.pk)

    def test_dashboard_shows_saved_and_live_image_previews(self):
        banner = Banner.objects.get(title="Natural privacy, made to last.")
        product = Product.objects.create(
            name="Preview Panel",
            sku="PREVIEW-001",
            image_name="solid-cottage.png",
            price="10.00",
        )
        self.client.force_login(self.staff)
        banner_form = self.client.get(reverse("dashboard-edit", args=["banners", banner.pk]))
        self.assertContains(banner_form, 'class="dashboard-image-preview"')
        self.assertContains(banner_form, "/media/banners/home-hero-fence-v3.png")
        banner_list = self.client.get(reverse("dashboard-list", args=["banners"]))
        self.assertContains(banner_list, 'class="dashboard-table-image"')
        product_form = self.client.get(reverse("dashboard-edit", args=["products", product.pk]))
        self.assertContains(product_form, "/static/assets/images/products/hd/solid-cottage.png")
        self.assertContains(product_form, "URL.createObjectURL")

    def test_seeded_home_banner_can_be_updated_from_dashboard(self):
        banner = Banner.objects.get(title="Natural privacy, made to last.")
        self.client.force_login(self.staff)
        response = self.client.post(reverse("dashboard-edit", args=["banners", banner.pk]), {
            "eyebrow": "Managed timber banner",
            "title": "A dashboard-controlled headline.",
            "image_alt": "Managed timber fence photograph",
            "link_url": "/catalog/",
            "link_label": "Browse timber",
            "display_order": "1",
            "is_active": "on",
        })
        self.assertRedirects(response, reverse("dashboard-list", args=["banners"]))
        home = self.client.get(reverse("home"))
        self.assertContains(home, "Managed timber banner")
        self.assertContains(home, "A dashboard-controlled headline.")
        self.assertContains(home, "Browse timber")

    def test_staff_can_update_contact_and_social_settings(self):
        settings = WebsiteSettings.load()
        self.client.force_login(self.staff)
        response = self.client.post(reverse("dashboard-edit", args=["website-settings", settings.pk]), {
            "phone_display": "01 234 5678",
            "phone_link": "+35312345678",
            "email": "hello@example.com",
            "business_hours": "Monday to Friday",
            "primary_location_name": "Main office",
            "primary_address": "1 Main Street\nDublin",
            "secondary_location_name": "Second yard",
            "secondary_address": "2 Side Street\nKildare",
            "map_url": "https://maps.example.com/location",
            "map_embed_url": "https://maps.example.com/embed",
            "facebook_url": "https://facebook.com/example",
            "instagram_url": "https://instagram.com/example",
            "pinterest_url": "https://pinterest.com/example",
            "linkedin_url": "https://linkedin.com/company/example",
            "youtube_url": "https://youtube.com/@example",
            "tiktok_url": "https://tiktok.com/@example",
        })
        self.assertRedirects(response, reverse("dashboard-list", args=["website-settings"]))
        contact_page = self.client.get(reverse("contact"))
        self.assertContains(contact_page, "hello@example.com")
        self.assertContains(contact_page, "01 234 5678")
        self.assertContains(contact_page, "1 Main Street")
        self.assertContains(contact_page, "2 Side Street")
        for url in (
            "https://maps.example.com/location",
            "https://maps.example.com/embed",
            "https://facebook.com/example",
            "https://instagram.com/example",
            "https://pinterest.com/example",
            "https://linkedin.com/company/example",
            "https://youtube.com/@example",
            "https://tiktok.com/@example",
        ):
            self.assertContains(contact_page, url)
        self.assertContains(contact_page, "<svg")
        home_page = self.client.get(reverse("home"))
        self.assertContains(home_page, "https://facebook.com/example")
        self.assertContains(home_page, 'class="social-links"')

    def test_website_page_content_section_is_not_exposed(self):
        self.client.force_login(self.staff)
        dashboard = self.client.get(reverse("dashboard-home"))

        self.assertNotContains(dashboard, ">Page content<")
        self.assertEqual(
            self.client.get(reverse("dashboard-list", args=["website-content"])).status_code,
            404,
        )
        self.assertContains(self.client.get(reverse("home")), "Find the right")

    def test_blank_social_urls_hide_the_social_section(self):
        settings = WebsiteSettings.load()
        settings.facebook_url = ""
        settings.instagram_url = ""
        settings.pinterest_url = ""
        settings.linkedin_url = ""
        settings.youtube_url = ""
        settings.tiktok_url = ""
        settings.save()
        page = self.client.get(reverse("contact"))
        self.assertNotContains(page, "Follow our latest work")
        self.assertNotContains(page, 'class="contact-social"')

    def test_staff_can_manage_smartfence_calculator_rates(self):
        calculator = SmartFenceCalculatorSettings.load()
        self.client.force_login(self.staff)
        response = self.client.post(reverse("dashboard-edit", args=["smartfence-calculator", calculator.pk]), {
            "panel_width": "2.00",
            "infill_height": "0.25",
            "included_infills": "6",
            "panel_pack_price": "222.00",
            "extra_infill_price": "33.00",
            "smartpost_cover_price": "66.00",
        })
        self.assertRedirects(response, reverse("dashboard-list", args=["smartfence-calculator"]))
        response = self.client.post(reverse("dashboard-create", args=["smartfence-rates"]), {
            "component": "trellis",
            "name": "Bronze",
            "swatch_class": "bronze-swatch",
            "unit_price": "44.00",
            "display_order": "99",
            "is_active": "on",
        })
        self.assertRedirects(response, reverse("dashboard-list", args=["smartfence-rates"]))
        self.assertTrue(SmartFenceCalculatorRate.objects.filter(component="trellis", name="Bronze", unit_price="44.00").exists())
        page = self.client.get(reverse("product"))
        self.assertContains(page, '"panelPackPrice": 222.0')
        self.assertContains(page, '"name": "Bronze"')

    def test_staff_can_manage_project_calculator_and_product_page_uses_it(self):
        category = Category.objects.create(name="Timber fencing")
        product = Product.objects.create(
            name="Managed Calculator Panel",
            sku="CALC-001",
            price="25.00",
            stock_quantity=10,
            category=category,
        )
        profile = ProductCalculatorProfile.objects.get(product=product)
        self.client.force_login(self.staff)
        response = self.client.post(reverse("dashboard-edit", args=["project-calculators", profile.pk]), {
            "product": product.pk,
            "panel_width": "2.40",
            "default_height": "1.60",
            "item_label": "Panel packs",
            "post_extra": "2",
            "pricing_mode": "product",
            "unit_price_override": "77.00",
            "calculation_note": "Dashboard-managed calculation note.",
            "display_order": "4",
            "is_active": "on",
        })
        self.assertRedirects(response, reverse("dashboard-list", args=["project-calculators"]))
        profile.refresh_from_db()
        self.assertEqual(profile.panel_width, Decimal("2.40"))
        page = self.client.get(reverse("product-detail", args=[product.slug]))
        self.assertContains(page, f'data-calculator-product="{product.slug}"')
        self.assertContains(page, '"key": "managed-calculator-panel"')
        self.assertContains(page, '"unitPrice": 77.0')
        self.assertContains(page, "Dashboard-managed calculation note.")

    def test_product_page_repairs_a_missing_calculator_profile(self):
        category = Category.objects.create(name="Timber fencing")
        Product.objects.bulk_create([
            Product(name="New Dashboard Panel", slug="new-dashboard-panel", sku="NEW-CALC-001", price="67.00", stock_quantity=20, category=category)
        ])
        product = Product.objects.get(sku="NEW-CALC-001")
        self.assertFalse(ProductCalculatorProfile.objects.filter(product=product).exists())
        page = self.client.get(reverse("product-detail", args=[product.slug]))
        self.assertTrue(ProductCalculatorProfile.objects.filter(product=product, pricing_mode="product").exists())
        self.assertContains(page, 'data-calculator-product="new-dashboard-panel"')
        self.assertContains(page, '"key": "new-dashboard-panel"')
        self.assertContains(page, '"unitPrice": 67.0')

    def test_staff_can_manage_homepage_calculator_settings(self):
        Product.objects.create(name="Homepage Calculator Panel", sku="HOME-CALC-001", price="45.00")
        settings = ProjectCalculatorSettings.load()
        self.client.force_login(self.staff)
        response = self.client.post(reverse("dashboard-edit", args=["project-calculator-settings", settings.pk]), {
            "eyebrow": "Managed calculator",
            "heading": "Build your boundary.",
            "heading_emphasis": "See the materials.",
            "introduction": "Managed calculator introduction.",
            "measurement_tip": "Managed measurement guidance.",
            "default_length": "14.50",
            "default_height": "1.60",
            "calculate_button_label": "Create estimate",
        })
        self.assertRedirects(response, reverse("dashboard-list", args=["project-calculator-settings"]))
        home = self.client.get(reverse("home"))
        self.assertContains(home, "Managed calculator")
        self.assertContains(home, "Build your boundary.")
        self.assertContains(home, "Managed calculator introduction.")
        self.assertNotContains(home, "data-calculator-product=")
        self.assertContains(home, "Choose a fence product")
        self.assertContains(home, 'value="14.50"')
        self.assertContains(home, "Create estimate")

    def test_calculator_groups_products_by_their_product_category(self):
        category = Category.objects.create(name="Timber Fencing")
        Product.objects.create(name="First Timber Panel", sku="GROUP-001", price="10.00", category=category)
        Product.objects.create(name="New Timber Panel", sku="GROUP-002", price="12.00", category=category)
        home = self.client.get(reverse("home"))
        self.assertContains(home, '"group": "Timber Fencing"', count=2)
        self.assertNotContains(home, '"group": "Timber fence panels"')

    def test_staff_can_update_quote_status_from_list(self):
        quote = QuoteRequest.objects.create(first_name="Jane", last_name="Doe", email="jane@example.com", address="Main Street", consent=True)
        self.client.force_login(self.staff)
        response = self.client.post(reverse("dashboard-status", args=["quotes", quote.pk]), {"status": "contacted"})
        self.assertRedirects(response, reverse("dashboard-list", args=["quotes"]))
        quote.refresh_from_db()
        self.assertEqual(quote.status, QuoteRequest.Status.CONTACTED)

    def test_staff_can_add_follow_up_note_and_change_status(self):
        quote = QuoteRequest.objects.create(first_name="Jane", last_name="Doe", email="jane@example.com", address="Main Street", consent=True)
        self.client.force_login(self.staff)
        response = self.client.post(reverse("dashboard-follow-up", args=["quotes", quote.pk]), {
            "note": "Called customer and requested measurements.", "status": "in_progress", "next_follow_up_at": "2026-08-20T10:30",
        })
        self.assertRedirects(response, reverse("dashboard-follow-up", args=["quotes", quote.pk]))
        quote.refresh_from_db()
        follow_up = SubmissionFollowUp.objects.get(quote=quote)
        self.assertEqual(quote.status, QuoteRequest.Status.IN_PROGRESS)
        self.assertEqual(follow_up.created_by, self.staff)

    def test_follow_up_can_be_added_inside_quote_edit_page(self):
        quote = QuoteRequest.objects.create(first_name="Jane", last_name="Doe", email="jane@example.com", address="Main Street", consent=True)
        self.client.force_login(self.staff)
        page = self.client.get(reverse("dashboard-edit", args=["quotes", quote.pk]))
        self.assertContains(page, "Add follow-up")
        response = self.client.post(reverse("dashboard-edit", args=["quotes", quote.pk]), {
            "action": "follow_up", "note": "Quote discussed with customer.", "status": "contacted", "next_follow_up_at": "",
        })
        self.assertRedirects(response, reverse("dashboard-edit", args=["quotes", quote.pk]))
        self.assertTrue(SubmissionFollowUp.objects.filter(quote=quote, note__contains="discussed").exists())
