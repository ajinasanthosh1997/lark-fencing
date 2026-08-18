from django.utils import translation
from rest_framework import serializers

from .models import (
    Author,
    BlogCategory,
    BlogPost,
    Category,
    ContactEnquiry,
    ContactMessage,
    Country,
    CustomerReview,
    GalleryItem,
    QuoteRequest,
    WebsiteContactSubmission,
)
from .services import verify_recaptcha


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ["id", "name", "code", "is_default"]


class ContactMessageSerializer(serializers.ModelSerializer):
    type_of_request_display = serializers.CharField(
        source="get_type_of_request_display",
        read_only=True,
    )

    class Meta:
        model = ContactMessage
        fields = "__all__"
        read_only_fields = ("submitted_at",)


class WebsiteContactSubmissionSerializer(serializers.ModelSerializer):
    recaptcha_token = serializers.CharField(write_only=True, trim_whitespace=True)

    class Meta:
        model = WebsiteContactSubmission
        fields = (
            "id",
            "first_name",
            "last_name",
            "email",
            "phone",
            "message",
            "recaptcha_token",
            "submitted_at",
        )
        read_only_fields = ("id", "submitted_at")
        extra_kwargs = {
            "first_name": {"trim_whitespace": True},
            "last_name": {"trim_whitespace": True},
            "email": {"trim_whitespace": True},
            "phone": {"required": False, "allow_blank": True, "trim_whitespace": True},
            "message": {
                "required": False,
                "allow_blank": True,
                "trim_whitespace": True,
            },
        }

    def validate_email(self, value):
        return value.lower()

    def validate_recaptcha_token(self, value):
        request = self.context.get("request")
        remote_ip = request.META.get("REMOTE_ADDR") if request else None
        if not verify_recaptcha(value, remote_ip=remote_ip):
            raise serializers.ValidationError("reCAPTCHA verification failed.")
        return value

    def create(self, validated_data):
        validated_data.pop("recaptcha_token")
        return super().create(validated_data)


class ConsentSerializerMixin:
    def validate_consent(self, value):
        if not value:
            raise serializers.ValidationError("Consent is required.")
        return value


class QuoteRequestSerializer(ConsentSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = QuoteRequest
        fields = ("id", "first_name", "last_name", "email", "phone", "address", "design", "approximate_length", "message", "consent", "submitted_at")
        read_only_fields = ("id", "submitted_at")

    def validate_email(self, value):
        return value.lower()


class ContactEnquirySerializer(ConsentSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = ContactEnquiry
        fields = ("id", "name", "email", "phone", "subject", "message", "consent", "submitted_at")
        read_only_fields = ("id", "submitted_at")

    def validate_email(self, value):
        return value.lower()


class CustomerReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerReview
        fields = ("id", "reviewer", "project", "rating", "review", "permission", "submitted_at")
        read_only_fields = ("id", "submitted_at")

    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

    def validate_permission(self, value):
        if not value:
            raise serializers.ValidationError("Permission is required.")
        return value


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class GalleryItemSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    country = CountrySerializer(read_only=True)
    country_id = serializers.PrimaryKeyRelatedField(
        queryset=Country.objects.all(),
        source="country",
        write_only=True,
        required=False,
    )

    class Meta:
        model = GalleryItem
        fields = "__all__"
        read_only_fields = ("created_at",)

    def get_image_url(self, obj):
        request = self.context.get("request")
        if obj.image:
            return request.build_absolute_uri(obj.image.url)
        return None


class AuthorSerializer(serializers.ModelSerializer):
    profile_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Author
        fields = "__all__"

    def get_profile_image_url(self, obj):
        request = self.context.get("request")
        if obj.profile_image:
            return request.build_absolute_uri(obj.profile_image.url)
        return None


class BlogCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogCategory
        fields = "__all__"


class BlogPostSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    author = AuthorSerializer(read_only=True)
    category = BlogCategorySerializer(read_only=True)
    author_id = serializers.PrimaryKeyRelatedField(
        queryset=Author.objects.all(),
        source="author",
        write_only=True,
    )
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=BlogCategory.objects.all(),
        source="category",
        write_only=True,
    )
    country = CountrySerializer(read_only=True)
    country_id = serializers.PrimaryKeyRelatedField(
        queryset=Country.objects.all(),
        source="country",
        write_only=True,
        required=False,
    )

    class Meta:
        model = BlogPost
        fields = "__all__"
        read_only_fields = ("created_at", "slug", "image_url")

    def get_title(self, obj):
        lang = translation.get_language() or "en"
        return getattr(obj, f"title_{lang}", obj.title)

    def get_description(self, obj):
        lang = translation.get_language() or "en"
        return getattr(obj, f"description_{lang}", obj.description)

    def get_content(self, obj):
        lang = translation.get_language() or "en"
        return getattr(obj, f"content_{lang}", obj.content)

    def get_image_url(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.url) if obj.image else None
