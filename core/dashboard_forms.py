import re

from django import forms
from django.contrib.auth import get_user_model
from django.forms import inlineformset_factory
from django.utils import timezone

from catalog.models import Product, ProductCalculatorProfile, ProductVariant, ProjectCalculatorSettings, SmartFenceCalculatorRate, SmartFenceCalculatorSettings
from orders.models import Order
from payments.models import Payment
from seo.models import PageSEO

from .models import Banner, Category, ContactEnquiry, CustomerReview, GalleryItem, LegalPolicy, QuoteRequest, SubmissionFollowUp, WebsiteSettings


class DashboardModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.ClearableFileInput):
                field.widget.attrs["accept"] = "image/*"


class ProductForm(DashboardModelForm):
    class Meta:
        model = Product
        fields = ("name", "sku", "description", "image_name", "category", "price", "currency", "track_inventory", "stock_quantity", "is_active")
        widgets = {"description": forms.Textarea(attrs={"rows": 5})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        help_texts = {
            "name": "Customer-facing product name shown in the catalogue and product page.",
            "sku": "Unique internal stock code. Each product must have a different SKU.",
            "description": "Short customer-facing description shown on the product page.",
            "image_name": "Image filename from static/assets/images/products/hd, for example solid-cottage.png.",
            "category": "Controls where the product appears in the catalogue and calculator category list.",
            "price": "Base catalogue price used when the product has no selected variant.",
            "currency": "Three-letter currency code, normally EUR.",
            "stock_quantity": "Available units. This limit is enforced only when Track inventory is enabled.",
            "is_active": "Enable to show and sell this product on the website. Disable to hide it without deleting its data.",
        }
        for name, help_text in help_texts.items():
            self.fields[name].help_text = help_text
        self.fields["track_inventory"].help_text = (
            "Enable this for stocked products: completed orders reduce the stock quantity and customers cannot buy more than is available. "
            "Disable it for made-to-order products or services with no fixed stock limit."
        )


class ProductVariantForm(DashboardModelForm):
    class Meta:
        model = ProductVariant
        fields = ("product", "size", "style", "sku", "price", "stock_quantity", "display_order", "is_active")


class ProductVariantInlineForm(DashboardModelForm):
    class Meta:
        model = ProductVariant
        fields = ("size", "style", "sku", "price", "stock_quantity", "display_order", "is_active")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        help_texts = {
            "size": "Customer-facing size option, for example 1.8m (W) × 1.8m (H).",
            "style": "Optional finish or treatment, for example Pressure Treated.",
            "sku": "Unique stock code for this exact size and style combination.",
            "price": "Price used when customers select this variant.",
            "stock_quantity": "Available units for this exact variant.",
            "display_order": "Lower numbers appear first in the product option buttons.",
            "is_active": "Enable to offer this variant on the website. Disable to hide it without deleting it.",
        }
        for name, help_text in help_texts.items():
            self.fields[name].help_text = help_text


ProductVariantInlineFormSet = inlineformset_factory(
    Product,
    ProductVariant,
    form=ProductVariantInlineForm,
    extra=1,
    can_delete=True,
)


class ProductCalculatorProfileForm(DashboardModelForm):
    class Meta:
        model = ProductCalculatorProfile
        fields = ("product", "panel_width", "default_height", "item_label", "post_extra", "pricing_mode", "unit_price_override", "calculation_note", "display_order", "is_active")
        widgets = {"calculation_note": forms.Textarea(attrs={"rows": 4})}


class ProjectCalculatorSettingsForm(DashboardModelForm):
    class Meta:
        model = ProjectCalculatorSettings
        fields = ("eyebrow", "heading", "heading_emphasis", "introduction", "measurement_tip", "default_length", "default_height", "calculate_button_label")
        widgets = {
            "introduction": forms.Textarea(attrs={"rows": 4}),
            "measurement_tip": forms.Textarea(attrs={"rows": 3}),
        }


class SmartFenceCalculatorSettingsForm(DashboardModelForm):
    class Meta:
        model = SmartFenceCalculatorSettings
        fields = ("panel_width", "infill_height", "included_infills", "panel_pack_price", "extra_infill_price", "smartpost_cover_price")


class SmartFenceCalculatorRateForm(DashboardModelForm):
    class Meta:
        model = SmartFenceCalculatorRate
        fields = ("component", "name", "swatch_class", "unit_price", "display_order", "is_active")


class CategoryForm(DashboardModelForm):
    class Meta:
        model = Category
        fields = ("name",)


class GalleryForm(DashboardModelForm):
    class Meta:
        model = GalleryItem
        fields = ("title", "description", "image", "category", "product", "display_size", "display_order", "is_active")


class BannerForm(DashboardModelForm):
    class Meta:
        model = Banner
        fields = ("eyebrow", "title", "image", "image_alt", "link_url", "link_label", "display_order", "is_active")


class WebsiteSettingsForm(DashboardModelForm):
    class Meta:
        model = WebsiteSettings
        fields = ("phone_display", "phone_link", "email", "business_hours", "primary_location_name", "primary_address", "secondary_location_name", "secondary_address", "map_url", "map_embed_url", "facebook_url", "instagram_url", "pinterest_url", "linkedin_url", "youtube_url", "tiktok_url")
        widgets = {
            "primary_address": forms.Textarea(attrs={"rows": 3}),
            "secondary_address": forms.Textarea(attrs={"rows": 3}),
        }


class LegalPolicyForm(DashboardModelForm):
    class Meta:
        model = LegalPolicy
        fields = (
            "title", "slug", "summary", "body", "version", "effective_date",
            "review_status", "reviewed_by", "reviewed_at", "display_order", "is_active",
        )
        widgets = {
            "summary": forms.Textarea(attrs={"rows": 3}),
            "body": forms.Textarea(attrs={"rows": 20}),
            "effective_date": forms.DateInput(attrs={"type": "date"}),
            "reviewed_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["review_status"].help_text = (
            "Choose Legally approved only after a qualified legal reviewer has approved this exact version."
        )
        self.fields["body"].help_text = "Trusted HTML used on the public policy page."

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("review_status") == LegalPolicy.ReviewStatus.APPROVED:
            if not cleaned.get("reviewed_by"):
                self.add_error("reviewed_by", "Record the qualified reviewer before approving this policy.")
            if not cleaned.get("reviewed_at"):
                self.add_error("reviewed_at", "Record when this exact policy version was approved.")
        return cleaned


class PageSEOForm(DashboardModelForm):
    class Meta:
        model = PageSEO
        fields = (
            "url_path", "title", "meta_description", "meta_keywords", "h1_tag",
            "content", "image_alt", "verification_tag", "canonical_url", "robots",
            "og_title", "og_description", "og_image",
        )
        widgets = {
            "meta_description": forms.Textarea(attrs={"rows": 3}),
            "og_description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["verification_tag"].help_text = (
            "Optional complete verification meta tag supplied by a search provider."
        )

    def clean_url_path(self):
        value = self.cleaned_data["url_path"].strip()
        if "://" in value or "?" in value or "#" in value:
            raise forms.ValidationError("Enter only a URL path, without a domain, query string, or fragment.")
        if not value.startswith("/"):
            value = f"/{value}"
        if value != "/" and not value.endswith("/"):
            value = f"{value}/"
        return value

    def clean_canonical_url(self):
        value = (self.cleaned_data.get("canonical_url") or "").strip()
        if value and not value.startswith(("https://", "http://")):
            raise forms.ValidationError("Enter a complete URL beginning with https:// or http://.")
        return value

    def clean_verification_tag(self):
        value = (self.cleaned_data.get("verification_tag") or "").strip()
        if value and not re.fullmatch(
            r"<meta\s+name=(['\"])[A-Za-z0-9:_-]+\1\s+content=(['\"])[^<>]+\2\s*/?>",
            value,
            flags=re.IGNORECASE,
        ):
            raise forms.ValidationError(
                "Enter one verification meta tag containing name and content attributes."
            )
        return value


class QuoteForm(DashboardModelForm):
    class Meta:
        model = QuoteRequest
        exclude = ("submitted_at",)


class EnquiryForm(DashboardModelForm):
    class Meta:
        model = ContactEnquiry
        exclude = ("submitted_at",)


class FollowUpForm(forms.ModelForm):
    status = forms.ChoiceField()

    class Meta:
        model = SubmissionFollowUp
        fields = ("note", "next_follow_up_at")
        widgets = {
            "note": forms.Textarea(attrs={"rows": 5, "placeholder": "Call outcome, information requested, customer response…"}),
            "next_follow_up_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, submission=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.submission = submission
        self.fields["status"].choices = submission.Status.choices
        self.fields["status"].initial = submission.status


class ReviewForm(DashboardModelForm):
    class Meta:
        model = CustomerReview
        fields = ("reviewer", "project", "rating", "review", "is_approved")

    def save(self, commit=True):
        review = super().save(commit=False)
        review.permission = True
        if commit:
            review.save()
        return review


class OrderForm(DashboardModelForm):
    class Meta:
        model = Order
        fields = ("status", "first_name", "last_name", "email", "phone", "fulfilment_method", "address_line_1", "address_line_2", "city", "county", "postal_code", "customer_notes", "confirmed_at", "dispatched_at", "delivered_at")
        widgets = {"customer_notes": forms.Textarea(attrs={"rows": 4})}


class OrderDeliveryForm(DashboardModelForm):
    class Meta:
        model = Order
        fields = ("first_name", "last_name", "email", "phone", "fulfilment_method", "address_line_1", "address_line_2", "city", "county", "postal_code", "country_code", "customer_notes")
        widgets = {"customer_notes": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["customer_notes"].help_text = "Customer-provided delivery or access instructions."


class OrderStaffNotesForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ("staff_notes",)
        labels = {"staff_notes": "Internal staff notes"}
        help_texts = {"staff_notes": "Visible to dashboard staff only; customers cannot see these notes."}
        widgets = {"staff_notes": forms.Textarea(attrs={"rows": 5, "placeholder": "Delivery arrangements, customer calls, access details…"})}


class PaymentForm(DashboardModelForm):
    class Meta:
        model = Payment
        fields = ("order", "method", "amount", "currency", "status", "paid_at")
        widgets = {
            "paid_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("order", "method", "amount", "currency"):
            self.fields[name].disabled = True

        self.fields["order"].help_text = "The customer order linked to this cash payment."
        self.fields["method"].label = "Payment method"
        self.fields["method"].help_text = "Checkout currently accepts cash on delivery only."
        self.fields["amount"].label = "Amount due"
        self.fields["amount"].help_text = "The order total to collect from the customer."
        self.fields["currency"].help_text = "Currency used for this order."
        self.fields["status"].label = "Cash payment status"
        self.fields["status"].help_text = "Use Pending until cash is received, Paid after collection, or Cancelled if the order will not be completed."
        self.fields["paid_at"].label = "Cash collected at"
        self.fields["paid_at"].help_text = "When you select Paid, leave this blank to record the current date and time automatically."
        self.fields["paid_at"].input_formats = ["%Y-%m-%dT%H:%M"]

        cod_statuses = (
            Payment.Status.PENDING,
            Payment.Status.PAID,
            Payment.Status.CANCELLED,
        )
        labels = dict(Payment.Status.choices)
        choices = [(value, labels[value]) for value in cod_statuses]
        if self.instance.pk and self.instance.status not in cod_statuses:
            choices.insert(0, (self.instance.status, labels[self.instance.status]))
        self.fields["status"].choices = choices

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("status") == Payment.Status.PAID and not cleaned_data.get("paid_at"):
            cleaned_data["paid_at"] = timezone.now()
        return cleaned_data


class StaffUserForm(forms.ModelForm):
    password = forms.CharField(required=False, widget=forms.PasswordInput, help_text="Leave blank to keep the current password.")

    class Meta:
        model = get_user_model()
        fields = ("username", "email", "first_name", "last_name", "is_active", "is_staff", "is_superuser", "password")

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")
        if password:
            user.set_password(password)
        elif not user.pk:
            user.set_unusable_password()
        if commit:
            user.save()
        return user
