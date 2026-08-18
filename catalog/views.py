from django.db.models import Count, Q
from rest_framework import generics

from core.models import Category
from .models import Product
from .serializers import ProductSerializer, StorefrontCategorySerializer


class CategoryList(generics.ListAPIView):
    queryset = Category.objects.annotate(
        product_count=Count("products", filter=Q(products__is_active=True))
    ).filter(product_count__gt=0).order_by("name")
    serializer_class = StorefrontCategorySerializer
    pagination_class = None


class ProductList(generics.ListAPIView):
    queryset = (
        Product.objects.filter(is_active=True)
        .select_related("category")
        .prefetch_related("gallery_images")
    )
    serializer_class = ProductSerializer
    search_fields = ["name", "sku", "description"]
    filterset_fields = ["category", "category__name"]


class ProductDetail(generics.RetrieveAPIView):
    queryset = (
        Product.objects.filter(is_active=True)
        .select_related("category")
        .prefetch_related("gallery_images")
    )
    serializer_class = ProductSerializer
    lookup_field = "slug"
