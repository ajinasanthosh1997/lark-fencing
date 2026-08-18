from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import *


@admin.register(WebsiteSettings)
class WebsiteSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not WebsiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(WebsiteContent)
class WebsiteContentAdmin(admin.ModelAdmin):
    list_display = ("page", "label", "key")
    list_filter = ("page",)
    search_fields = ("label", "key", "value")


@admin.register(LegalPolicy)
class LegalPolicyAdmin(admin.ModelAdmin):
    list_display = ("title", "version", "effective_date", "review_status", "is_active")
    list_filter = ("review_status", "is_active")
    search_fields = ("title", "slug", "summary", "body", "reviewed_by")
    prepopulated_fields = {"slug": ("title",)}

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone', 'type_of_request', 'submitted_at')
    list_filter = ('type_of_request', 'submitted_at')
    search_fields = ('full_name', 'phone', 'email')
    date_hierarchy = 'submitted_at'
    readonly_fields = ('submitted_at',)
    fieldsets = (
        (None, {'fields': ('full_name', 'phone', 'email', 'cpr')}),
        ('Request', {'fields': ('type_of_request', 'submitted_at')}),
    )


@admin.register(WebsiteContactSubmission)
class WebsiteContactSubmissionAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'phone', 'submitted_at')
    search_fields = ('first_name', 'last_name', 'email', 'phone', 'message')
    date_hierarchy = 'submitted_at'
    readonly_fields = (
        'first_name',
        'last_name',
        'email',
        'phone',
        'message',
        'submitted_at',
    )

    def has_add_permission(self, request):
        return False


@admin.register(QuoteRequest)
class QuoteRequestAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'design', 'submitted_at')
    search_fields = ('first_name', 'last_name', 'email', 'phone', 'address', 'message')
    readonly_fields = ('submitted_at',)


@admin.register(ContactEnquiry)
class ContactEnquiryAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'submitted_at')
    search_fields = ('name', 'email', 'phone', 'subject', 'message')
    readonly_fields = ('submitted_at',)


@admin.register(CustomerReview)
class CustomerReviewAdmin(admin.ModelAdmin):
    list_display = ('reviewer', 'project', 'rating', 'is_approved', 'submitted_at')
    list_filter = ('rating', 'is_approved')
    search_fields = ('reviewer', 'project', 'review')
    readonly_fields = ('submitted_at',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'gallery_count')
    search_fields = ('name',)

    def gallery_count(self, obj):
        return obj.gallery_items.count()
    gallery_count.short_description = 'Items'

class GalleryItemInline(admin.TabularInline):
    model = GalleryItem
    extra = 1
    fields = ('title', 'image_preview', 'category', 'product')
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="50" height="50" />')
        return "-"
    image_preview.short_description = 'Preview'

@admin.register(GalleryItem)
class GalleryItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'product', 'image_preview')
    list_filter = ('category', 'product')
    search_fields = ('title', 'description', 'product__name', 'product__sku')
    readonly_fields = ('image_preview',)
    autocomplete_fields = ('category', 'product')

    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="100" />')
        return "-"
    image_preview.short_description = 'Preview'

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('name', 'profile_image_preview')
    search_fields = ('name',)
    readonly_fields = ('profile_image_preview',)

    def profile_image_preview(self, obj):
        if obj.profile_image:
            return mark_safe(f'<img src="{obj.profile_image.url}" width="50" height="50" />')
        return "-"
    profile_image_preview.short_description = 'Image'




@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'featured', 'created_at', 'image_preview')
    list_filter = ('category', 'featured', 'created_at')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    autocomplete_fields = ('author', 'category')  # REMOVED 'tags' FROM THIS LIST
    date_hierarchy = 'created_at'
    readonly_fields = ('image_preview',)
    # REMOVED filter_horizontal LINE COMPLETELY
    fieldsets = (
        (None, {'fields': ('title', 'slug', 'description', 'content')}),
        ('Media', {'fields': ('image', 'image_preview')}),
        ('Metadata', {'fields': ('author', 'category', 'featured', 'reading_time')}),  # REMOVED 'tags'
    )

    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="100" />')
        return "-"
    image_preview.short_description = 'Preview'
