from dataclasses import dataclass

from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import user_passes_test
from django.db import transaction
from django.db.models import ProtectedError, Q
from django.http import Http404
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from catalog.models import Product, ProductCalculatorProfile, ProductVariant, ProjectCalculatorSettings, SmartFenceCalculatorRate, SmartFenceCalculatorSettings
from orders.models import Order
from orders.services import OrderWorkflowError, available_transitions, record_cash_payment, transition_order, workflow_progress
from payments.models import Payment
from seo.models import PageSEO

from .dashboard_forms import BannerForm, CategoryForm, EnquiryForm, FollowUpForm, GalleryForm, LegalPolicyForm, OrderDeliveryForm, OrderForm, OrderStaffNotesForm, PageSEOForm, PaymentForm, ProductCalculatorProfileForm, ProductForm, ProductVariantForm, ProductVariantInlineFormSet, ProjectCalculatorSettingsForm, QuoteForm, ReviewForm, SmartFenceCalculatorRateForm, SmartFenceCalculatorSettingsForm, StaffUserForm, WebsiteSettingsForm
from .models import Banner, Category, ContactEnquiry, CustomerReview, GalleryItem, LegalPolicy, QuoteRequest, WebsiteSettings


@dataclass(frozen=True)
class Section:
    label: str
    model: object
    form: object
    columns: tuple
    search: tuple = ()
    allow_create: bool = True


SECTIONS = {
    "products": Section("Products", Product, ProductForm, ("image_name", "name", "sku", "price", "stock_quantity", "is_active"), ("name", "sku", "description")),
    "variants": Section("Product variants", ProductVariant, ProductVariantForm, ("product", "size", "style", "sku", "price", "stock_quantity", "is_active"), ("product__name", "size", "style", "sku")),
    "project-calculator-settings": Section("Homepage calculator settings", ProjectCalculatorSettings, ProjectCalculatorSettingsForm, ("default_length", "default_height", "calculate_button_label"), (), False),
    "project-calculators": Section("Project calculator products", ProductCalculatorProfile, ProductCalculatorProfileForm, ("product", "panel_width", "pricing_mode", "is_active"), ("product__name", "calculation_note")),
    "smartfence-calculator": Section("SmartFence calculator", SmartFenceCalculatorSettings, SmartFenceCalculatorSettingsForm, ("panel_width", "panel_pack_price", "extra_infill_price", "smartpost_cover_price"), (), False),
    "smartfence-rates": Section("SmartFence component rates", SmartFenceCalculatorRate, SmartFenceCalculatorRateForm, ("component", "name", "unit_price", "is_active"), ("component", "name")),
    "categories": Section("Categories", Category, CategoryForm, ("name",), ("name",)),
    "gallery": Section("Gallery", GalleryItem, GalleryForm, ("image", "title", "category", "display_size", "display_order", "is_active"), ("title", "description")),
    "banners": Section("Banners", Banner, BannerForm, ("image", "title", "eyebrow", "display_order", "is_active"), ("title", "eyebrow")),
    "website-settings": Section("Website settings", WebsiteSettings, WebsiteSettingsForm, ("email", "phone_display", "primary_location_name"), (), False),
    "legal-policies": Section("Legal policies", LegalPolicy, LegalPolicyForm, ("title", "version", "effective_date", "review_status", "is_active"), ("title", "slug", "summary", "body", "reviewed_by")),
    "seo-content": Section("SEO content", PageSEO, PageSEOForm, ("url_path", "title", "robots", "updated_at"), ("url_path", "title", "meta_description", "meta_keywords", "h1_tag")),
    "quotes": Section("Quote requests", QuoteRequest, QuoteForm, ("first_name", "last_name", "email", "design", "status", "submitted_at"), ("first_name", "last_name", "email", "address")),
    "enquiries": Section("Contact enquiries", ContactEnquiry, EnquiryForm, ("name", "email", "subject", "status", "submitted_at"), ("name", "email", "subject", "message")),
    "reviews": Section("Customer reviews", CustomerReview, ReviewForm, ("reviewer", "project", "rating", "is_approved", "submitted_at"), ("reviewer", "project", "review")),
    "orders": Section("Orders", Order, OrderForm, ("order_number", "email", "status", "total", "created_at"), ("order_number", "email", "first_name", "last_name"), False),
    "payments": Section("Cash-on-delivery payments", Payment, PaymentForm, ("order", "method", "status", "amount", "currency", "paid_at", "created_at"), ("order__order_number", "order__email"), False),
    "users": Section("Users", get_user_model(), StaffUserForm, ("username", "email", "first_name", "is_staff", "is_active"), ("username", "email", "first_name", "last_name")),
}


def staff_required(view):
    return user_passes_test(lambda user: user.is_authenticated and user.is_superuser, login_url="dashboard-login")(view)


def get_section(slug):
    try:
        return SECTIONS[slug]
    except KeyError as exc:
        raise Http404("Dashboard section not found") from exc


def dashboard_login(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect("dashboard-home")
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        if not user.is_superuser:
            form.add_error(None, "Administrator access is required.")
        else:
            login(request, user)
            return redirect(request.GET.get("next") or "dashboard-home")
    return render(request, "dashboard/login.html", {"form": form})


def dashboard_logout(request):
    logout(request)
    return redirect("dashboard-login")


@staff_required
def dashboard_home(request):
    stats = [
        ("Products", Product.objects.count(), "products"), ("Orders", Order.objects.count(), "orders"),
        ("New quotes", QuoteRequest.objects.count(), "quotes"), ("Enquiries", ContactEnquiry.objects.count(), "enquiries"),
        ("Gallery images", GalleryItem.objects.count(), "gallery"), ("Active banners", Banner.objects.filter(is_active=True).count(), "banners"),
    ]
    return render(request, "dashboard/home.html", {"sections": SECTIONS, "stats": stats, "recent_orders": Order.objects.all()[:5], "recent_quotes": QuoteRequest.objects.all()[:5]})


@staff_required
def section_list(request, section):
    config = get_section(section)
    rows = config.model.objects.all()
    query = request.GET.get("q", "").strip()
    if query and config.search:
        expression = Q()
        for field in config.search:
            expression |= Q(**{f"{field}__icontains": query})
        rows = rows.filter(expression)
    field_names = {field.name for field in config.model._meta.fields}
    status_value = request.GET.get("status", "")
    active_value = request.GET.get("active", "")
    if "status" in field_names and status_value:
        rows = rows.filter(status=status_value)
    if "is_active" in field_names and active_value in ("true", "false"):
        rows = rows.filter(is_active=active_value == "true")
    if not rows.ordered:
        rows = rows.order_by("pk")
    try:
        per_page = int(request.GET.get("per_page", 20))
    except ValueError:
        per_page = 20
    per_page = per_page if per_page in (10, 20, 50, 100) else 20
    page_obj = Paginator(rows, per_page).get_page(request.GET.get("page"))
    status_choices = config.model._meta.get_field("status").choices if "status" in field_names else ()
    if section == "orders":
        operational_statuses = {
            Order.Status.PENDING_PAYMENT,
            Order.Status.CONFIRMED,
            Order.Status.PROCESSING,
            Order.Status.READY,
            Order.Status.DISPATCHED,
            Order.Status.DELIVERED,
            Order.Status.CANCELLED,
        }
        status_choices = [(value, label) for value, label in status_choices if value in operational_statuses]
    elif section == "payments":
        cod_statuses = {Payment.Status.PENDING, Payment.Status.PAID, Payment.Status.CANCELLED}
        status_choices = [(value, label) for value, label in status_choices if value in cod_statuses]
    preserved = request.GET.copy()
    preserved.pop("page", None)
    return render(request, "dashboard/list.html", {
        "sections": SECTIONS, "section_slug": section, "config": config,
        "rows": page_obj, "page_obj": page_obj, "query": query,
        "has_status_filter": "status" in field_names, "status_choices": status_choices,
        "status_value": status_value, "has_active_filter": "is_active" in field_names,
        "active_value": active_value, "per_page": per_page, "preserved_query": preserved.urlencode(),
    })


@staff_required
def section_create(request, section):
    config = get_section(section)
    if not config.allow_create:
        raise Http404("New records for this section are created by the storefront.")
    form = config.form(request.POST or None, request.FILES or None)
    has_variant_data = section == "products" and "variants-TOTAL_FORMS" in request.POST
    variant_formset = ProductVariantInlineFormSet(
        request.POST if has_variant_data else None,
        instance=form.instance,
        prefix="variants",
    ) if section == "products" else None
    if request.method == "POST" and form.is_valid() and (not has_variant_data or variant_formset.is_valid()):
        with transaction.atomic():
            item = form.save()
            if has_variant_data:
                variant_formset.instance = item
                variant_formset.save()
        messages.success(request, f"{config.label} item created.")
        return redirect("dashboard-list", section=section)
    return render(request, "dashboard/form.html", {"sections": SECTIONS, "section_slug": section, "config": config, "form": form, "variant_formset": variant_formset, "mode": "Create"})


@staff_required
def section_edit(request, section, pk):
    if section == "orders":
        return order_detail(request, pk)
    if section == "payments":
        payment = get_object_or_404(Payment, pk=pk)
        return redirect("dashboard-edit", section="orders", pk=payment.order_id)
    config = get_section(section)
    item = get_object_or_404(config.model, pk=pk)
    is_submission = section in ("quotes", "enquiries")
    is_follow_up = is_submission and request.method == "POST" and request.POST.get("action") == "follow_up"
    form = config.form(None if is_follow_up else (request.POST or None), None if is_follow_up else (request.FILES or None), instance=item)
    has_variant_data = section == "products" and "variants-TOTAL_FORMS" in request.POST
    variant_formset = ProductVariantInlineFormSet(
        request.POST if has_variant_data else None,
        instance=item,
        prefix="variants",
    ) if section == "products" else None
    follow_up_form = FollowUpForm(request.POST if is_follow_up else None, submission=item) if is_submission else None
    if is_follow_up and follow_up_form.is_valid():
        follow_up = follow_up_form.save(commit=False)
        if section == "quotes":
            follow_up.quote = item
        else:
            follow_up.enquiry = item
        follow_up.created_by = request.user
        follow_up.save()
        item.status = follow_up_form.cleaned_data["status"]
        item.save(update_fields=["status"])
        messages.success(request, "Follow-up note saved.")
        return redirect("dashboard-edit", section=section, pk=pk)
    if request.method == "POST" and not is_follow_up and form.is_valid() and (not has_variant_data or variant_formset.is_valid()):
        with transaction.atomic():
            form.save()
            if has_variant_data:
                variant_formset.save()
        messages.success(request, f"{config.label} item updated.")
        return redirect("dashboard-list", section=section)
    return render(request, "dashboard/form.html", {
        "sections": SECTIONS, "section_slug": section, "config": config,
        "form": form, "item": item, "variant_formset": variant_formset, "mode": "Edit", "follow_up_form": follow_up_form,
        "follow_ups": item.follow_ups.select_related("created_by") if is_submission else None,
    })


def order_detail(request, pk):
    order = get_object_or_404(
        Order.objects.prefetch_related(
            "items__product",
            "items__variant",
            "payments",
            "status_history__changed_by",
        ),
        pk=pk,
    )
    notes_form = OrderStaffNotesForm(instance=order)
    delivery_form = OrderDeliveryForm(instance=order)

    if request.method == "POST":
        action = request.POST.get("action", "")
        try:
            if action == "change_status":
                next_status = request.POST.get("next_status", "")
                status_note = request.POST.get("status_note", "")
                if next_status == Order.Status.CANCELLED and not status_note.strip():
                    raise OrderWorkflowError("Add a cancellation reason before cancelling this order.")
                updated = transition_order(
                    order,
                    next_status,
                    changed_by=request.user,
                    note=status_note,
                )
                messages.success(request, f"Order status changed to {updated.get_status_display()}.")
            elif action == "mark_cash_paid":
                payment = record_cash_payment(order, changed_by=request.user)
                messages.success(request, f"Cash payment of {payment.amount} {payment.currency} recorded.")
            elif action == "save_notes":
                notes_form = OrderStaffNotesForm(request.POST, instance=order)
                if notes_form.is_valid():
                    notes_form.save()
                    messages.success(request, "Internal order notes saved.")
                else:
                    raise OrderWorkflowError("The internal notes could not be saved.")
            elif action == "save_delivery":
                delivery_form = OrderDeliveryForm(request.POST, instance=order)
                if delivery_form.is_valid():
                    delivery_form.save()
                    messages.success(request, "Customer and delivery details updated.")
                else:
                    raise OrderWorkflowError("Check the customer and delivery fields and try again.")
            else:
                raise OrderWorkflowError("Choose a valid order action.")
        except OrderWorkflowError as exc:
            messages.error(request, str(exc))
        return redirect("dashboard-edit", section="orders", pk=order.pk)

    return render(request, "dashboard/order_detail.html", {
        "sections": SECTIONS,
        "section_slug": "orders",
        "config": SECTIONS["orders"],
        "order": order,
        "payment": order.payments.all()[0] if order.payments.all() else None,
        "status_transitions": available_transitions(order),
        "workflow_steps": workflow_progress(order),
        "notes_form": notes_form,
        "delivery_form": delivery_form,
    })


@staff_required
def section_delete(request, section, pk):
    if section in ("orders", "payments"):
        raise Http404("Order and payment records cannot be deleted from the dashboard.")
    config = get_section(section)
    item = get_object_or_404(config.model, pk=pk)
    if request.method == "POST":
        try:
            item.delete(); messages.success(request, f"{config.label} item deleted.")
        except ProtectedError:
            messages.error(request, "This record is referenced elsewhere and cannot be deleted.")
        return redirect("dashboard-list", section=section)
    return render(request, "dashboard/delete.html", {"sections": SECTIONS, "section_slug": section, "config": config, "item": item})


@staff_required
def update_submission_status(request, section, pk):
    if request.method != "POST" or section not in ("quotes", "enquiries"):
        raise Http404("Action not found")
    config = get_section(section)
    item = get_object_or_404(config.model, pk=pk)
    status_value = request.POST.get("status", "")
    valid_statuses = {value for value, _ in config.model.Status.choices}
    if status_value in valid_statuses:
        item.status = status_value
        item.save(update_fields=["status"])
        messages.success(request, f"Status changed to {item.get_status_display()}.")
    else:
        messages.error(request, "Invalid status action.")
    return redirect("dashboard-list", section=section)


@staff_required
def submission_follow_up(request, section, pk):
    if section not in ("quotes", "enquiries"):
        raise Http404("Follow-up not found")
    config = get_section(section)
    item = get_object_or_404(config.model, pk=pk)
    form = FollowUpForm(request.POST or None, submission=item)
    if request.method == "POST" and form.is_valid():
        follow_up = form.save(commit=False)
        if section == "quotes":
            follow_up.quote = item
        else:
            follow_up.enquiry = item
        follow_up.created_by = request.user
        follow_up.save()
        item.status = form.cleaned_data["status"]
        item.save(update_fields=["status"])
        messages.success(request, "Follow-up note saved.")
        return redirect("dashboard-follow-up", section=section, pk=pk)
    return render(request, "dashboard/follow_up.html", {
        "sections": SECTIONS, "section_slug": section, "config": config,
        "item": item, "form": form, "follow_ups": item.follow_ups.select_related("created_by"),
    })
