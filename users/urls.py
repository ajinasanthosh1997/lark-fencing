from django.urls import path
from .views import AccountOrderDetailView, AccountOrderListView, AddressDetailView, AddressListCreateView, LoginView, LogoutView, MeView, PasswordChangeView, PasswordResetConfirmView, PasswordResetRequestView, SignupView

urlpatterns = [
    path("signup/", SignupView.as_view(), name="auth-signup"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("me/", MeView.as_view(), name="auth-me"),
    path("addresses/", AddressListCreateView.as_view(), name="account-address-list"),
    path("addresses/<int:pk>/", AddressDetailView.as_view(), name="account-address-detail"),
    path("orders/", AccountOrderListView.as_view(), name="account-order-list"),
    path("orders/<uuid:public_id>/", AccountOrderDetailView.as_view(), name="account-order-detail"),
    path("password/change/", PasswordChangeView.as_view(), name="password-change"),
    path("password/reset/", PasswordResetRequestView.as_view(), name="password-reset-request"),
    path("password/reset/confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
]
