from django.urls import path
from .views import CartCreate, CartDetail, CartItemCreate, CartItemDetail

urlpatterns = [
    path("carts/", CartCreate.as_view(), name="cart-create"),
    path("carts/<uuid:public_id>/", CartDetail.as_view(), name="cart-detail"),
    path("carts/<uuid:public_id>/items/", CartItemCreate.as_view(), name="cart-item-create"),
    path("carts/<uuid:public_id>/items/<int:pk>/", CartItemDetail.as_view(), name="cart-item-detail"),
]
