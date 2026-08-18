from django import template


register = template.Library()


@register.filter
def review_stars(value):
    try:
        rating = max(1, min(5, int(value)))
    except (TypeError, ValueError):
        rating = 0
    return "★" * rating + "☆" * (5 - rating)


@register.filter
def reviewer_initials(value):
    words = [word for word in str(value or "").split() if word]
    return "".join(word[0] for word in words[:2]).upper() or "LR"
