from django.db import models
from django.utils.text import slugify


class Country(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=2, unique=True)  # ISO country code
    is_default = models.BooleanField(default=False)  # Mark default country

    def __str__(self):
        return self.name
    
class ContactMessage(models.Model):
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    cpr = models.CharField(max_length=20, blank=True, null=True)

    TYPE_OF_REQUEST_CHOICES = [
        ('rent_car', 'Rent a car'),
        ('travel', 'Travel'),
        ('business_center', 'Business Center'),
    ]
    type_of_request = models.CharField(max_length=50, choices=TYPE_OF_REQUEST_CHOICES)

    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.get_type_of_request_display()}"


class WebsiteContactSubmission(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    message = models.TextField(max_length=5000, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.email}"


class QuoteRequest(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "New"
        IN_PROGRESS = "in_progress", "In progress"
        CONTACTED = "contacted", "Contacted"
        COMPLETED = "completed", "Completed"
        CLOSED = "closed", "Closed"

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    address = models.CharField(max_length=500)
    design = models.CharField(max_length=150, blank=True)
    approximate_length = models.CharField(max_length=50, blank=True)
    message = models.TextField(max_length=5000, blank=True)
    consent = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    staff_notes = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.design or 'Quote'}"


class ContactEnquiry(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "New"
        IN_PROGRESS = "in_progress", "In progress"
        CONTACTED = "contacted", "Contacted"
        COMPLETED = "completed", "Completed"
        CLOSED = "closed", "Closed"

    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    subject = models.CharField(max_length=150, blank=True)
    message = models.TextField(max_length=5000)
    consent = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    staff_notes = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.name} - {self.subject or 'Enquiry'}"


class SubmissionFollowUp(models.Model):
    quote = models.ForeignKey(QuoteRequest, on_delete=models.CASCADE, null=True, blank=True, related_name="follow_ups")
    enquiry = models.ForeignKey(ContactEnquiry, on_delete=models.CASCADE, null=True, blank=True, related_name="follow_ups")
    note = models.TextField(max_length=5000)
    next_follow_up_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey("auth.User", on_delete=models.SET_NULL, null=True, related_name="submission_follow_ups")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Follow-up {self.created_at:%Y-%m-%d %H:%M}"


class CustomerReview(models.Model):
    reviewer = models.CharField(max_length=60)
    project = models.CharField(max_length=100)
    rating = models.PositiveSmallIntegerField()
    review = models.TextField(max_length=700)
    permission = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.reviewer} - {self.rating}/5"


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class WebsiteSettings(models.Model):
    """Contact and social details shared across the public website."""

    phone_display = models.CharField(max_length=50, default="089 948 0832")
    phone_link = models.CharField(max_length=50, default="+353899480832", help_text="International format used by click-to-call links.")
    email = models.EmailField(default="larkfencing@yahoo.com")
    business_hours = models.CharField(max_length=200, default="Mon–Fri 8:30am–5pm · Sat 9am–5pm")
    primary_location_name = models.CharField(max_length=100, default="Walkinstown")
    primary_address = models.TextField(default="9 Lower Ballymount Road\nWalkinstown, Dublin 12, D12 E398")
    secondary_location_name = models.CharField(max_length=100, default="Johnstown yard", blank=True)
    secondary_address = models.TextField(default="Unit 10, Westown Wood\nJohnstown, Naas, Co. Kildare, W91 TK29", blank=True)
    map_url = models.URLField(max_length=2000, default="https://www.google.com/maps/search/?api=1&query=Lark+Fencing")
    map_embed_url = models.URLField(max_length=2000, blank=True, help_text="Google Maps embed URL used by the contact-page iframe.")
    facebook_url = models.URLField(max_length=500, blank=True)
    instagram_url = models.URLField(max_length=500, blank=True)
    pinterest_url = models.URLField(max_length=500, blank=True)
    linkedin_url = models.URLField(max_length=500, blank=True)
    youtube_url = models.URLField(max_length=500, blank=True)
    tiktok_url = models.URLField(max_length=500, blank=True)

    class Meta:
        verbose_name_plural = "Website settings"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        return None

    @classmethod
    def load(cls):
        instance, _ = cls.objects.get_or_create(pk=1)
        return instance

    def __str__(self):
        return "Website contact details"


class WebsiteContent(models.Model):
    """An editable piece of copy used by a public website template."""

    page = models.CharField(max_length=50, db_index=True)
    key = models.SlugField(max_length=100, unique=True, help_text="Template identifier; do not change after creation.")
    label = models.CharField(max_length=150, help_text="Human-readable dashboard label.")
    value = models.TextField()

    class Meta:
        ordering = ("page", "label")
        verbose_name_plural = "Website content"

    def __str__(self):
        return f"{self.page.title()} — {self.label}"


class LegalPolicy(models.Model):
    class ReviewStatus(models.TextChoices):
        REVIEW_REQUIRED = "review_required", "Legal review required"
        IN_REVIEW = "in_review", "Under legal review"
        APPROVED = "approved", "Legally approved"

    title = models.CharField(max_length=150)
    slug = models.SlugField(max_length=160, unique=True)
    summary = models.TextField(max_length=500)
    body = models.TextField(help_text="Policy body rendered as trusted HTML on the website.")
    version = models.CharField(max_length=30, default="Draft 1.0")
    effective_date = models.DateField()
    review_status = models.CharField(
        max_length=20,
        choices=ReviewStatus.choices,
        default=ReviewStatus.REVIEW_REQUIRED,
    )
    reviewed_by = models.CharField(max_length=150, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("display_order", "title")
        verbose_name_plural = "Legal policies"

    def __str__(self):
        return self.title


class GalleryItem(models.Model):
    class DisplaySize(models.TextChoices):
        STANDARD = "standard", "Standard"
        WIDE = "wide", "Wide"
        TALL = "tall", "Tall"

    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='gallery/')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='gallery_items')
    created_at = models.DateTimeField(auto_now_add=True)
    country = models.ForeignKey(Country,on_delete=models.SET_NULL,null=True,blank=True)
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="gallery_images",
    )
    display_size = models.CharField(max_length=20, choices=DisplaySize.choices, default=DisplaySize.STANDARD)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order", "-created_at"]

    def __str__(self):
        return self.title or f"Gallery Item {self.id}"


class Banner(models.Model):
    eyebrow = models.CharField(max_length=100, blank=True)
    title = models.CharField(max_length=180)
    image = models.ImageField(upload_to="banners/")
    image_alt = models.CharField(max_length=255)
    link_url = models.CharField(max_length=500, default="/catalog/")
    link_label = models.CharField(max_length=100, default="Explore")
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["display_order", "-created_at"]

    def __str__(self):
        return self.title


class Author(models.Model):
    name = models.CharField(max_length=100)
    profile_image = models.ImageField(upload_to='authors/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class BlogCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)  # allow blank so we can generate it
    description = models.TextField(blank=True, null=True)
    content = models.TextField()
    image = models.ImageField(upload_to='blog_images/')
    author = models.ForeignKey(Author, on_delete=models.SET_NULL, null=True)
    category = models.ForeignKey(BlogCategory, on_delete=models.SET_NULL, null=True)
    featured = models.BooleanField(default=False)
    reading_time = models.PositiveIntegerField(help_text="Time in minutes", default=3)
    created_at = models.DateField(auto_now_add=True)
    country = models.ForeignKey(Country,on_delete=models.SET_NULL,null=True,blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while BlogPost.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

