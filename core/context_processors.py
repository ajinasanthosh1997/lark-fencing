from seo.models import PageSEO

from .models import LegalPolicy, WebsiteContent, WebsiteSettings


def website_settings(request):
    page_seo = PageSEO.objects.filter(url_path=request.path).first()
    seo_canonical_url = ""
    seo_og_image_url = ""
    if page_seo:
        seo_canonical_url = page_seo.canonical_url or request.build_absolute_uri(request.path)
        if page_seo.og_image:
            seo_og_image_url = request.build_absolute_uri(page_seo.og_image.url)
    return {
        "site_settings": WebsiteSettings.load(),
        "site_content": dict(WebsiteContent.objects.values_list("key", "value")),
        "legal_policies": LegalPolicy.objects.filter(is_active=True),
        "page_seo": page_seo,
        "seo_canonical_url": seo_canonical_url,
        "seo_og_image_url": seo_og_image_url,
    }
