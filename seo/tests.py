from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import PageSEO


class PageSEOTests(TestCase):
    def setUp(self):
        self.seo = PageSEO.objects.create(
            url_path="/about/",
            title="Managed About SEO Title",
            meta_description="Managed description for the LARK Fencing about page.",
            meta_keywords="fencing, kildare, dublin",
            h1_tag="About LARK Fencing",
            content="<p>Managed supporting content.</p>",
            image_alt="LARK Fencing timber yard",
            verification_tag='<meta name="site-verification" content="verified-token">',
            canonical_url="https://www.larkfencing.ie/about/",
            robots="index, follow",
            og_title="Managed social title",
            og_description="Managed social description.",
        )

    def test_model_open_graph_fallback_properties(self):
        self.assertEqual(self.seo.get_og_title, "Managed social title")
        self.assertEqual(self.seo.get_og_description, "Managed social description.")
        self.seo.og_title = ""
        self.seo.og_description = ""
        self.assertEqual(self.seo.get_og_title, self.seo.title)
        self.assertEqual(self.seo.get_og_description, self.seo.meta_description)

    def test_exact_url_path_overrides_shared_head(self):
        about = self.client.get(reverse("about"))
        home = self.client.get(reverse("home"))

        self.assertContains(about, "<title>Managed About SEO Title</title>", html=True)
        self.assertContains(about, 'name="description" content="Managed description for the LARK Fencing about page."')
        self.assertContains(about, 'name="keywords" content="fencing, kildare, dublin"')
        self.assertContains(about, 'name="robots" content="index, follow"')
        self.assertContains(about, 'rel="canonical" href="https://www.larkfencing.ie/about/"')
        self.assertContains(about, 'property="og:title" content="Managed social title"')
        self.assertContains(about, 'name="site-verification" content="verified-token"')
        self.assertNotContains(home, "Managed About SEO Title")

    def test_dashboard_can_create_normalized_seo_path_with_ckeditor(self):
        admin = get_user_model().objects.create_user(
            username="seo-manager",
            password="test-password",
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(admin)
        home = self.client.get(reverse("dashboard-home"))
        create_url = reverse("dashboard-create", args=["seo-content"])
        create_page = self.client.get(create_url)

        self.assertContains(home, "SEO content")
        self.assertContains(create_page, "django_ckeditor_5")

        response = self.client.post(
            create_url,
            {
                "url_path": "contact",
                "title": "Contact LARK Fencing",
                "meta_description": "Contact LARK Fencing for product advice and installation enquiries.",
                "meta_keywords": "contact fencing",
                "h1_tag": "Contact LARK Fencing",
                "content": "<p>Contact our team.</p>",
                "image_alt": "",
                "verification_tag": "",
                "canonical_url": "https://www.larkfencing.ie/contact/",
                "robots": "index, follow",
                "og_title": "",
                "og_description": "",
            },
        )

        self.assertRedirects(response, reverse("dashboard-list", args=["seo-content"]))
        self.assertTrue(PageSEO.objects.filter(url_path="/contact/").exists())
