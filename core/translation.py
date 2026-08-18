from modeltranslation.translator import register, TranslationOptions
from .models import Author, BlogCategory, BlogPost, Category, GalleryItem

@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ('name',)

@register(GalleryItem)
class GalleryItemTranslationOptions(TranslationOptions):
    fields = ('title', 'description',)

@register(Author)
class AuthorTranslationOptions(TranslationOptions):
    fields = ('name', 'bio',)

@register(BlogCategory)
class BlogCategoryTranslationOptions(TranslationOptions):
    fields = ('name',)

@register(BlogPost)
class BlogPostTranslationOptions(TranslationOptions):
    fields = ('title', 'description', 'content',)
