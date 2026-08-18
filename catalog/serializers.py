from rest_framework import serializers

from core.models import GalleryItem
from core.serializers import CategorySerializer

from .models import Product, ProductVariant


class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ("id", "name", "size", "style", "sku", "price", "stock_quantity", "display_order")


class ProductGalleryImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = GalleryItem
        fields = ("id", "title", "description", "image_url")

    def get_image_url(self, obj):
        request = self.context.get("request")
        if not obj.image:
            return None
        return request.build_absolute_uri(obj.image.url) if request else obj.image.url


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    gallery_images = ProductGalleryImageSerializer(many=True, read_only=True)
    image_url = serializers.CharField(source="storefront_image_url", read_only=True)
    variants = serializers.SerializerMethodField()

    def get_variants(self, obj):
        return ProductVariantSerializer(obj.variants.filter(is_active=True), many=True).data

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "sku",
            "description",
            "image_url",
            "category",
            "price",
            "currency",
            "track_inventory",
            "stock_quantity",
            "gallery_images",
            "variants",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class StorefrontCategorySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    product_count = serializers.IntegerField()
