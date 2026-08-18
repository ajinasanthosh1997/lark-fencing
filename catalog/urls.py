from django.urls import path

from .views import CategoryList, ProductDetail, ProductList


urlpatterns = [
    path("categories/", CategoryList.as_view(), name="storefront-category-list"),
    path("products/", ProductList.as_view(), name="product-list"),
    path("products/<slug:slug>/", ProductDetail.as_view(), name="product-detail"),
]
