from django.urls import path

from .views import OrderCreate, OrderDetail


urlpatterns = [
    path("orders/", OrderCreate.as_view(), name="order-create"),
    path("orders/<uuid:public_id>/", OrderDetail.as_view(), name="order-detail"),
]
