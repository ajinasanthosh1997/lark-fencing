from django.shortcuts import render

# Create your views here.
from rest_framework import generics
from .models import *
from .serializers import *

class CountryListCreate(generics.ListCreateAPIView):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    filterset_fields = ['is_default']

class CountryRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    lookup_field = 'code'

class ContactMessageListCreate(generics.ListCreateAPIView):
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer
    filterset_fields = ['type_of_request', 'email']
    search_fields = ['full_name', 'phone', 'email']

class ContactMessageRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer


class WebsiteContactSubmissionCreate(generics.CreateAPIView):
    queryset = WebsiteContactSubmission.objects.all()
    serializer_class = WebsiteContactSubmissionSerializer
    authentication_classes = []


class QuoteRequestCreate(generics.CreateAPIView):
    queryset = QuoteRequest.objects.all()
    serializer_class = QuoteRequestSerializer
    authentication_classes = []


class ContactEnquiryCreate(generics.CreateAPIView):
    queryset = ContactEnquiry.objects.all()
    serializer_class = ContactEnquirySerializer
    authentication_classes = []


class CustomerReviewCreate(generics.CreateAPIView):
    queryset = CustomerReview.objects.all()
    serializer_class = CustomerReviewSerializer
    authentication_classes = []


class CategoryListCreate(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    search_fields = ['name']

class CategoryRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class GalleryItemListCreate(generics.ListCreateAPIView):
    queryset = GalleryItem.objects.all()
    serializer_class = GalleryItemSerializer
    filterset_fields = ['category','country','country__code']
    search_fields = ['title', 'description']

class GalleryItemRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = GalleryItem.objects.all()
    serializer_class = GalleryItemSerializer


class AuthorListCreate(generics.ListCreateAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    search_fields = ['name']

class AuthorRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer

class BlogCategoryListCreate(generics.ListCreateAPIView):
    queryset = BlogCategory.objects.all()
    serializer_class = BlogCategorySerializer
    search_fields = ['name', 'slug']

class BlogCategoryRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = BlogCategory.objects.all()
    serializer_class = BlogCategorySerializer
    lookup_field = 'slug'


class BlogPostListCreate(generics.ListCreateAPIView):
    queryset = BlogPost.objects.all()
    serializer_class = BlogPostSerializer
    filterset_fields = ['country','country__code']

    def dispatch(self, request, *args, **kwargs):
        lang = request.GET.get('lang')
        if lang:
            translation.activate(lang)
        return super().dispatch(request, *args, **kwargs)
 

class BlogPostRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = BlogPost.objects.all()
    serializer_class = BlogPostSerializer
    lookup_field = 'slug'

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['include_country'] = True
        return context

