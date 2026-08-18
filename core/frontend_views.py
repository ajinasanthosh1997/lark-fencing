from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, render
from django.utils.cache import add_never_cache_headers

from catalog.models import Product, ProductCalculatorProfile, ProjectCalculatorSettings, SmartFenceCalculatorRate, SmartFenceCalculatorSettings, ensure_product_calculator_profile
from core.models import Banner, Category, CustomerReview, GalleryItem, LegalPolicy


TEMPLATE_ROOT = "larkfencing-templates/lark-fencing"


def render_fresh(request, template_name, context=None):
    """Render database-managed storefront content without browser caching."""
    response = render(request, f"{TEMPLATE_ROOT}/{template_name}.html", context or {})
    add_never_cache_headers(response)
    return response


def render_page(request, template_name):
    return render_fresh(request, template_name)


def policy_detail(request, slug):
    policy = get_object_or_404(LegalPolicy, slug=slug, is_active=True)
    return render_fresh(request, "policy-detail", {"policy": policy})


def get_project_calculator_config():
    profiles = ProductCalculatorProfile.objects.filter(
        is_active=True,
        product__is_active=True,
    ).select_related("product", "product__category")
    smartfence = SmartFenceCalculatorSettings.load()
    products = []
    for profile in profiles:
        product = profile.product
        calculator_price = profile.unit_price_override
        if calculator_price is None:
            calculator_price = product.price
        products.append(
            {
                "key": product.slug,
                "name": product.name,
                "group": profile.display_group,
                "width": float(profile.panel_width),
                "height": float(profile.default_height) if profile.default_height is not None else None,
                "items": profile.item_label,
                "postExtra": profile.post_extra,
                "pricingMode": profile.pricing_mode,
                "unitPrice": float(calculator_price) if calculator_price is not None else None,
                "note": profile.calculation_note
                or f"{product.name} estimate uses {profile.panel_width}m-wide bays. Confirm product size, gates, corners, delivery, and site conditions before ordering.",
            }
        )
    return {
        "products": products,
        "smartFence": {
            "infillHeight": float(smartfence.infill_height),
            "includedInfills": smartfence.included_infills,
            "panelPackPrice": float(smartfence.panel_pack_price),
            "extraInfillPrice": float(smartfence.extra_infill_price),
        },
    }


def home(request):
    calculator_settings = ProjectCalculatorSettings.load()
    customer_reviews = CustomerReview.objects.filter(
        permission=True,
        is_approved=True,
    )[:12]
    return render_fresh(
        request,
        "index",
        {
            "banners": Banner.objects.filter(is_active=True),
            "project_calculator_settings": calculator_settings,
            "project_calculator_config": get_project_calculator_config(),
            "customer_reviews": customer_reviews,
        },
    )


def about(request):
    featured_review = CustomerReview.objects.filter(
        permission=True,
        is_approved=True,
    ).first()
    return render_fresh(request, "about", {"featured_review": featured_review})


def account(request):
    return render_page(request, "account")


def cart(request):
    return render_page(request, "cart")


def catalog(request):
    products = Product.objects.filter(is_active=True).select_related("category").prefetch_related("variants")
    selected_category = request.GET.get("category", "")
    search = request.GET.get("q", "").strip()
    if selected_category:
        products = products.filter(category__id=selected_category)
    if search:
        products = products.filter(
            Q(name__icontains=search)
            | Q(description__icontains=search)
            | Q(sku__icontains=search)
        )
    categories = Category.objects.annotate(
        product_count=Count("products", filter=Q(products__is_active=True))
    ).filter(product_count__gt=0).order_by("name")
    return render_fresh(
        request,
        "catalog",
        {
            "products": products,
            "categories": categories,
            "selected_category": selected_category,
            "search_query": search,
            "total_products": Product.objects.filter(is_active=True).count(),
        },
    )


def checkout(request):
    return render_page(request, "checkout")


def contact(request):
    return render_page(request, "contact")


def gallery(request):
    items = GalleryItem.objects.filter(is_active=True).select_related("category", "product")
    categories = Category.objects.filter(gallery_items__in=items).distinct().order_by("name")
    return render_fresh(request, "gallery", {"gallery_items": items, "gallery_categories": categories})


def login(request):
    return render_page(request, "login")


def product_detail(request, slug=None):
    slug = slug or request.GET.get("id")
    products = Product.objects.filter(is_active=True).select_related("category").prefetch_related("gallery_images", "variants")
    if slug:
        product = get_object_or_404(products, slug=slug)
    else:
        product = get_object_or_404(products, name__iexact=request.GET.get("name", ""))
    calculator_profile, _ = ensure_product_calculator_profile(product)
    related_products = Product.objects.filter(
        is_active=True, category=product.category
    ).exclude(pk=product.pk)[:4]
    active_variants = [variant for variant in product.variants.all() if variant.is_active]
    variant_sizes = list(dict.fromkeys(variant.size or variant.name for variant in active_variants))
    variant_styles = list(dict.fromkeys(variant.style for variant in active_variants if variant.style))
    return render_fresh(
        request,
        "product-detail",
        {
            "product_item": product,
            "related_products": related_products,
            "active_variants": active_variants,
            "variant_sizes": variant_sizes,
            "variant_styles": variant_styles,
            "show_project_calculator": calculator_profile.is_active,
            "project_calculator_config": get_project_calculator_config(),
        },
    )


def product(request):
    calculator = SmartFenceCalculatorSettings.load()
    rates = SmartFenceCalculatorRate.objects.filter(is_active=True)
    calculator_config = {
        "panelWidth": float(calculator.panel_width),
        "infillHeight": float(calculator.infill_height),
        "includedInfills": calculator.included_infills,
        "panelPackPrice": float(calculator.panel_pack_price),
        "extraInfillPrice": float(calculator.extra_infill_price),
        "smartpostCoverPrice": float(calculator.smartpost_cover_price),
        "rates": [
            {
                "component": rate.component,
                "name": rate.name,
                "swatch": rate.swatch_class,
                "price": float(rate.unit_price),
            }
            for rate in rates
        ],
    }
    return render_fresh(request, "product", {"smartfence_calculator_config": calculator_config})


def quote(request):
    return render_page(request, "quote")


def returns(request):
    return render_page(request, "returns")


def signup(request):
    return render_page(request, "signup")
