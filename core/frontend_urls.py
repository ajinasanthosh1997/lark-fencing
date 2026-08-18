from django.urls import path
from django.views.generic import RedirectView

from . import frontend_views as views


urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("account/", views.account, name="account"),
    path("cart/", views.cart, name="cart"),
    path("catalog/", views.catalog, name="catalog"),
    path("checkout/", views.checkout, name="checkout"),
    path("contact/", views.contact, name="contact"),
    path("gallery/", views.gallery, name="gallery"),
    path("login/", views.login, name="login"),
    path("products/<slug:slug>/", views.product_detail, name="product-detail"),
    path("policies/<slug:slug>/", views.policy_detail, name="policy-detail"),
    path("smart-fence/", views.product, name="product"),
    path("quote/", views.quote, name="quote"),
    # Keep old bookmarks working while routing customers to the current policy.
    path("returns/", RedirectView.as_view(url="/policies/cancellation-and-returns/", permanent=False)),
    path("signup/", views.signup, name="signup"),

    path("index.html", RedirectView.as_view(pattern_name="home", permanent=True)),
    path("about.html", RedirectView.as_view(pattern_name="about", permanent=True)),
    path("account.html", RedirectView.as_view(pattern_name="account", permanent=True)),
    path("cart.html", RedirectView.as_view(pattern_name="cart", permanent=True)),
    path("catalog.html", RedirectView.as_view(pattern_name="catalog", permanent=True)),
    path("checkout.html", RedirectView.as_view(pattern_name="checkout", permanent=True)),
    path("contact.html", RedirectView.as_view(pattern_name="contact", permanent=True)),
    path("gallery.html", RedirectView.as_view(pattern_name="gallery", permanent=True)),
    path("login.html", RedirectView.as_view(pattern_name="login", permanent=True)),
    path("product.html", RedirectView.as_view(pattern_name="product", permanent=True)),
    path("quote.html", RedirectView.as_view(pattern_name="quote", permanent=True)),
    path("returns.html", RedirectView.as_view(url="/policies/cancellation-and-returns/", permanent=True)),
    path("signup.html", RedirectView.as_view(pattern_name="signup", permanent=True)),
    # Legacy query-string product links are resolved to the same database view.
    path("product-detail.html", views.product_detail),
]
