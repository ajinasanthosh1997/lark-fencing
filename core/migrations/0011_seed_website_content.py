from django.db import migrations


CONTENT = (
    ("home", "home_hero_eyebrow", "Hero eyebrow", "Fencing supplied or professionally fitted"),
    ("home", "home_hero_title", "Hero title", "Find the right fence.<br><em>Love your garden.</em>"),
    ("home", "home_hero_intro", "Hero introduction", "Compare timber, SmartFence, PVC, composite, and concrete ranges—then order online or ask our local team for practical advice."),
    ("about", "about_hero_eyebrow", "Hero eyebrow", "About LARK Fencing"),
    ("about", "about_hero_title", "Hero title", "Rooted locally.<br>Built to <em>last.</em>"),
    ("about", "about_hero_intro", "Hero introduction", "For over 30 years, we have helped homeowners and businesses create outdoor spaces with more privacy, security, and style."),
    ("catalog", "catalog_hero_eyebrow", "Hero eyebrow", "LARK product catalogue"),
    ("catalog", "catalog_hero_title", "Hero title", "Quality fencing for<br>every <em>garden.</em>"),
    ("catalog", "catalog_hero_intro", "Hero introduction", "Browse our current ranges. Every product below is loaded directly from the database."),
    ("gallery", "gallery_hero_eyebrow", "Hero eyebrow", "Selected projects"),
    ("gallery", "gallery_hero_title", "Hero title", "Made for real<br><em>outdoor life.</em>"),
    ("gallery", "gallery_hero_intro", "Hero introduction", "From compact garden screens to complete property boundaries, every installation is measured for its setting and finished with care."),
    ("contact", "contact_hero_eyebrow", "Hero eyebrow", "We’re here to help"),
    ("contact", "contact_hero_title", "Hero title", "Let’s talk about<br>your <em>outdoors.</em>"),
    ("contact", "contact_hero_intro", "Hero introduction", "Ask about supply-only fencing, complete installation, timber panels, trellis, or SmartFence. We serve Kildare, Dublin, and surrounding areas."),
    ("quote", "quote_hero_eyebrow", "Hero eyebrow", "Start your project"),
    ("quote", "quote_hero_title", "Hero title", "A better boundary<br>begins <em>here.</em>"),
    ("quote", "quote_hero_intro", "Hero introduction", "Tell us a little about your space. We’ll reply within one working day to arrange a friendly, no-obligation site visit."),
    ("returns", "returns_hero_eyebrow", "Hero eyebrow", "Customer information"),
    ("returns", "returns_hero_title", "Hero title", "Returns &amp;<br><em>refunds.</em>"),
    ("returns", "returns_hero_intro", "Hero introduction", "This policy explains change-of-mind returns, damaged or incorrect goods, faulty products, and how to contact our team."),
    ("product", "product_hero_eyebrow", "Hero eyebrow", "Made in Ireland"),
    ("product", "product_hero_title", "Hero title", "SmartFence<br>metal panels"),
    ("product", "product_hero_intro", "Hero introduction", "A robust, low-maintenance fencing system made from PVC-coated galvanised steel. Supplied flat packed and designed to fit standard concrete H-posts."),
    ("cart", "cart_hero_eyebrow", "Hero eyebrow", "Your selections"),
    ("cart", "cart_hero_title", "Hero title", "Shopping <em>cart.</em>"),
    ("cart", "cart_hero_intro", "Hero introduction", "Review quantities and prices before continuing to secure online card payment."),
    ("checkout", "checkout_hero_eyebrow", "Hero eyebrow", "Online payment"),
    ("checkout", "checkout_hero_title", "Hero title", "Complete your <em>order.</em>"),
    ("checkout", "checkout_hero_intro", "Hero introduction", "Enter your delivery details and continue using secure online card payment."),
    ("account", "account_hero_eyebrow", "Hero eyebrow", "Customer account"),
    ("account", "account_hero_title", "Hero title", "My <em>account.</em>"),
    ("account", "account_hero_intro", "Hero introduction", "Manage your details and keep track of projects with LARK Fencing."),
)


def seed_content(apps, schema_editor):
    WebsiteContent = apps.get_model("core", "WebsiteContent")
    WebsiteContent.objects.bulk_create(
        [WebsiteContent(page=page, key=key, label=label, value=value) for page, key, label, value in CONTENT],
        ignore_conflicts=True,
    )


class Migration(migrations.Migration):
    dependencies = [("core", "0010_websitecontent")]
    operations = [migrations.RunPython(seed_content, migrations.RunPython.noop)]
