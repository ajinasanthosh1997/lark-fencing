from django import template

register = template.Library()


@register.filter
def field_value(obj, name):
    value = getattr(obj, name, "")
    display = getattr(obj, f"get_{name}_display", None)
    if display:
        value = display()
    if value is True:
        return "Yes"
    if value is False:
        return "No"
    return value if value not in (None, "") else "—"


@register.filter
def field_label(model, name):
    try:
        return model._meta.get_field(name).verbose_name.title()
    except Exception:
        return name.replace("_", " ").title()


@register.filter
def image_preview_url(obj, name):
    if name == "image_name":
        return obj.storefront_image_url if getattr(obj, "image_name", "") else ""
    value = getattr(obj, name, None)
    try:
        return value.url if value else ""
    except (AttributeError, ValueError):
        return ""
