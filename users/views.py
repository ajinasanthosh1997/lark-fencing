from django.conf import settings
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import generics, status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.models import Order
from orders.serializers import OrderCreateSerializer
from .models import CustomerAddress
from .serializers import CustomerAddressSerializer, LoginSerializer, PasswordChangeSerializer, PasswordResetConfirmSerializer, SignupSerializer, UserSerializer, UserUpdateSerializer


def auth_response(user):
    token, _ = Token.objects.get_or_create(user=user)
    return {"token": token.key, "user": UserSerializer(user).data}


class SignupView(APIView):
    authentication_classes = []

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(auth_response(serializer.save()), status=status.HTTP_201_CREATED)


class LoginView(APIView):
    authentication_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return Response(auth_response(serializer.validated_data["user"]))


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.auth.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)


class AddressListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CustomerAddressSerializer

    def get_queryset(self):
        return CustomerAddress.objects.filter(user=self.request.user)


class AddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CustomerAddressSerializer

    def get_queryset(self):
        return CustomerAddress.objects.filter(user=self.request.user)


class AccountOrderListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderCreateSerializer

    def get_queryset(self):
        return Order.objects.filter(email__iexact=self.request.user.email).prefetch_related("items", "payments")


class AccountOrderDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderCreateSerializer
    lookup_field = "public_id"

    def get_queryset(self):
        return Order.objects.filter(email__iexact=self.request.user.email).prefetch_related("items", "payments")


class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=["password"])
        request.user.auth_token.delete()
        return Response({"detail": "Password changed. Please sign in again."})


class PasswordResetRequestView(APIView):
    authentication_classes = []

    def post(self, request):
        email = str(request.data.get("email", "")).strip().lower()
        user = get_user_model().objects.filter(email__iexact=email, is_active=True).first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = request.build_absolute_uri(f"/login/?reset_uid={uid}&reset_token={token}")
            send_mail("Reset your LARK Fencing password", f"Use this link to reset your password: {reset_url}", getattr(settings, "DEFAULT_FROM_EMAIL", "webmaster@localhost"), [user.email], fail_silently=True)
        return Response({"detail": "If an account exists, password reset instructions have been sent."})


class PasswordResetConfirmView(APIView):
    authentication_classes = []

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        user.auth_token.delete() if hasattr(user, "auth_token") else None
        return Response({"detail": "Password reset successfully."})
