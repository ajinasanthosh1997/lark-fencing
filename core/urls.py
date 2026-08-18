from django.urls import path
from .views import *

urlpatterns = [
    # Contact Messages
    path('contact-messages/', ContactMessageListCreate.as_view(), name='contact-message-list'),
    path('contact-messages/<int:pk>/', ContactMessageRetrieveUpdateDestroy.as_view(), name='contact-message-detail'),
    path('contact-us/', WebsiteContactSubmissionCreate.as_view(), name='website-contact-create'),
    path('quote-requests/', QuoteRequestCreate.as_view(), name='quote-request-create'),
    path('contact-enquiries/', ContactEnquiryCreate.as_view(), name='contact-enquiry-create'),
    
    # Gallery Categories
    path('gallery-categories/', CategoryListCreate.as_view(), name='gallery-category-list'),
    path('gallery-categories/<int:pk>/', CategoryRetrieveUpdateDestroy.as_view(), name='gallery-category-detail'),
    
    # Gallery Items
    path('gallery-items/', GalleryItemListCreate.as_view(), name='gallery-item-list'),
    path('gallery-items/<int:pk>/', GalleryItemRetrieveUpdateDestroy.as_view(), name='gallery-item-detail'),

    # Authors
    path('authors/', AuthorListCreate.as_view(), name='author-list'),
    path('authors/<int:pk>/', AuthorRetrieveUpdateDestroy.as_view(), name='author-detail'),
    
    # Blog Categories
    path('blog-categories/', BlogCategoryListCreate.as_view(), name='blog-category-list'),
    path('blog-categories/<slug:slug>/', BlogCategoryRetrieveUpdateDestroy.as_view(), name='blog-category-detail'),
    
    # Blog Posts
    path('blog-posts/', BlogPostListCreate.as_view(), name='blog-post-list'),
    path('blog-posts/<slug:slug>/', BlogPostRetrieveUpdateDestroy.as_view(), name='blog-post-detail'),

    path('countries/', CountryListCreate.as_view()),
    path('countries/<str:code>/', CountryRetrieveUpdateDestroy.as_view()),
    
]
