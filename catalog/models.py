from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify


class Product(models.Model):
    class ReturnClassification(models.TextChoices):
        STANDARD = "standard", "Standard"
        CUSTOM_MADE = "custom_made", "Custom-made / made-to-order"
        CUT_TO_SIZE = "cut_to_size", "Cut-to-size"
        SPECIAL_ORDER = "special_order", "Special order"
        CLEARANCE = "clearance", "Clearance / end-of-line"

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    sku = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    image_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Filename from static/assets/images/products/hd, e.g. solid-cottage.png",
    )
    category = models.ForeignKey(
        "core.Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
    )
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    currency = models.CharField(max_length=3, default="EUR")
    track_inventory = models.BooleanField(default=True)
    stock_quantity = models.PositiveIntegerField(default=0)
    return_classification = models.CharField(
        max_length=20,
        choices=ReturnClassification.choices,
        default=ReturnClassification.STANDARD,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    @property
    def change_of_mind_returnable(self):
        return self.return_classification == self.ReturnClassification.STANDARD

    @property
    def storefront_image_url(self):
        if self.image_name:
            return f"/static/assets/images/products/hd/{self.image_name}"
        return "/static/assets/images/products/hd/solid-cottage.png"

    def __str__(self):
        return f"{self.name} ({self.sku})"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or self.sku.lower()
            candidate = base_slug
            counter = 1
            while Product.objects.exclude(pk=self.pk).filter(slug=candidate).exists():
                counter += 1
                candidate = f"{base_slug}-{counter}"
            self.slug = candidate
        self.currency = self.currency.upper()
        super().save(*args, **kwargs)


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    name = models.CharField(max_length=120, help_text="Generated from size and style for carts and orders.")
    size = models.CharField(max_length=80, blank=True, help_text="For example: 1.8m (W) × 1.8m (H)")
    style = models.CharField(max_length=80, blank=True, help_text="For example: Pressure Treated")
    sku = models.CharField(max_length=100, unique=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
    stock_quantity = models.PositiveIntegerField(default=0)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order", "name"]
        constraints = [models.UniqueConstraint(fields=["product", "size", "style"], name="unique_variant_options_per_product")]

    def __str__(self):
        return f"{self.product.name} — {self.name}"

    def save(self, *args, **kwargs):
        option_parts = [part for part in (self.size.strip(), self.style.strip()) if part]
        if option_parts:
            self.name = " — ".join(option_parts)
        super().save(*args, **kwargs)


class ProjectCalculatorSettings(models.Model):
    eyebrow = models.CharField(max_length=100, default="Fence calculator")
    heading = models.CharField(max_length=160, default="Plan any fence.")
    heading_emphasis = models.CharField(max_length=160, default="Know what you need.")
    introduction = models.TextField(
        default="Choose an exact fence product and enter the total length and height. We will estimate the number of that product required, its post positions, coverage, and available material pricing."
    )
    measurement_tip = models.TextField(
        default="Measure each straight boundary run and add the lengths together. Gates and corners are confirmed during the final review."
    )
    default_length = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        default=Decimal("20.00"),
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    default_height = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal("1.80"),
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    calculate_button_label = models.CharField(max_length=100, default="Calculate materials")

    class Meta:
        verbose_name_plural = "Project calculator settings"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        return None

    @classmethod
    def load(cls):
        instance, _ = cls.objects.get_or_create(pk=1)
        return instance

    def __str__(self):
        return "Homepage project calculator settings"


class ProductCalculatorProfile(models.Model):
    class PricingMode(models.TextChoices):
        QUOTE = "quote", "Request quote"
        PRODUCT = "product", "Use product price"
        SMARTFENCE = "smartfence", "Use SmartFence calculation"

    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="calculator_profile")
    panel_width = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal("1.80"),
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Coverage width of one panel or pack, in metres.",
    )
    default_height = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Optional height selected automatically for this product, in metres.",
    )
    item_label = models.CharField(max_length=80, default="Panels required")
    post_extra = models.PositiveIntegerField(
        default=1,
        help_text="Extra post positions added to the number of panels. Usually 1.",
    )
    pricing_mode = models.CharField(max_length=20, choices=PricingMode.choices, default=PricingMode.QUOTE)
    unit_price_override = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Optional calculator-only unit price. Leave blank to use the product catalogue price.",
    )
    calculation_note = models.TextField(blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("display_order", "product__category__name", "product__name")

    @property
    def display_group(self):
        return self.product.category.name if self.product.category else "Other fencing"

    def __str__(self):
        return f"{self.product.name} calculator profile"


class SmartFenceCalculatorSettings(models.Model):
    panel_width = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("1.80"), help_text="Panel width in metres.")
    infill_height = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("0.30"), help_text="Height added by one infill, in metres.")
    included_infills = models.PositiveIntegerField(default=5, help_text="Infills included in the base panel-pack price.")
    panel_pack_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("160.00"))
    extra_infill_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("29.00"))
    smartpost_cover_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("54.50"))

    class Meta:
        verbose_name_plural = "SmartFence calculator settings"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        return None

    @classmethod
    def load(cls):
        instance, _ = cls.objects.get_or_create(pk=1)
        return instance

    def __str__(self):
        return "SmartFence calculation settings"


class SmartFenceCalculatorRate(models.Model):
    class Component(models.TextChoices):
        TRELLIS = "trellis", "Trellis colour"
        PLINTH = "plinth", "Plinth colour"
        POST_COVER = "caps", "Concrete post-cover colour"

    component = models.CharField(max_length=20, choices=Component.choices)
    name = models.CharField(max_length=80, help_text="Colour or option name shown in the calculator.")
    swatch_class = models.SlugField(max_length=80, help_text="CSS swatch name, e.g. anthracite-swatch.")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("component", "display_order", "name")
        constraints = [models.UniqueConstraint(fields=("component", "name"), name="unique_smartfence_component_rate")]

    def __str__(self):
        return f"{self.get_component_display()} — {self.name}: €{self.unit_price}"


def ensure_product_calculator_profile(product):
    """Give every storefront product a calculator entry unless one already exists."""
    return ProductCalculatorProfile.objects.get_or_create(
        product=product,
        defaults={
            "panel_width": Decimal("1.80"),
            "item_label": "Panels required",
            "post_extra": 1,
            "pricing_mode": (
                ProductCalculatorProfile.PricingMode.PRODUCT
                if Decimal(str(product.price or 0)) > 0
                else ProductCalculatorProfile.PricingMode.QUOTE
            ),
            "display_order": 999,
            "is_active": True,
        },
    )


@receiver(post_save, sender=Product)
def create_product_calculator_profile(sender, instance, created, raw=False, **kwargs):
    if created and not raw:
        ensure_product_calculator_profile(instance)
