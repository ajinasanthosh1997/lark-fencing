from django.db import models
from django_ckeditor_5.fields import CKEditor5Field


class PageSEO(models.Model):
    url_path = models.CharField(
        max_length=255,
        unique=True,
        help_text="URL path without domain (e.g., '/about/').",
    )
    title = models.CharField(max_length=100, help_text="Page title (up to 100 characters).")
    meta_description = models.TextField(
        max_length=160,
        help_text="Meta description (150–160 characters recommended).",
    )
    meta_keywords = models.CharField(max_length=255, blank=True, help_text="Comma-separated keywords.")
    h1_tag = models.CharField(max_length=255, help_text="Main heading of the page.")
    content = CKEditor5Field("Content", config_name="extends", blank=True)
    image_alt = models.CharField(max_length=255, blank=True, help_text="ALT text for the main or Open Graph image.")
    verification_tag = models.CharField(max_length=255, blank=True, null=True)
    canonical_url = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Canonical URL for this page (optional).",
    )
    robots = models.CharField(
        max_length=100,
        default="index, follow",
        help_text="Robots meta tag (e.g., 'index, follow', 'noindex, nofollow').",
    )
    og_title = models.CharField(max_length=100, blank=True, help_text="Open Graph title (if empty, uses title field).")
    og_description = models.TextField(
        max_length=160,
        blank=True,
        help_text="Open Graph description (if empty, uses meta description).",
    )
    og_image = models.ImageField(
        upload_to="seo/og_images/",
        blank=True,
        null=True,
        help_text="Open Graph image (1200×630 recommended).",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("url_path",)
        verbose_name = "Page SEO"
        verbose_name_plural = "Page SEO"

    def __str__(self):
        return f"SEO for {self.url_path}"

    @property
    def get_og_title(self):
        return self.og_title or self.title

    @property
    def get_og_description(self):
        return self.og_description or self.meta_description
