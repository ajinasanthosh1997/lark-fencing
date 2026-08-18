from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Cart, CartItem
from .serializers import CartItemSerializer, CartSerializer


def cart_queryset():
    return Cart.objects.prefetch_related("items__variant", "items__product__category", "items__product__gallery_images", "items__product__variants")


class CartCreate(APIView):
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        user = request.user if request.user.is_authenticated else None
        cart = Cart.objects.create(user=user)
        return Response(CartSerializer(cart, context={"request": request}).data, status=status.HTTP_201_CREATED)


class CartDetail(generics.RetrieveDestroyAPIView):
    authentication_classes = [TokenAuthentication]
    serializer_class = CartSerializer
    lookup_field = "public_id"
    queryset = cart_queryset().filter(is_active=True)


class CartItemCreate(APIView):
    authentication_classes = [TokenAuthentication]

    def post(self, request, public_id):
        cart = get_object_or_404(Cart, public_id=public_id, is_active=True)
        serializer = CartItemSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        product = serializer.validated_data["product"]
        variant = serializer.validated_data.get("variant")
        existing = cart.items.filter(product=product, variant=variant).first()
        if existing:
            data = {"quantity": existing.quantity + serializer.validated_data["quantity"]}
            if "customization" in request.data:
                data["customization"] = request.data["customization"]
            serializer = CartItemSerializer(existing, data=data, partial=True, context={"request": request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
        else:
            serializer.save(cart=cart)
        cart.save(update_fields=["updated_at"])
        return Response(CartSerializer(cart_queryset().get(pk=cart.pk), context={"request": request}).data, status=status.HTTP_201_CREATED)


class CartItemDetail(generics.UpdateAPIView, generics.DestroyAPIView):
    authentication_classes = [TokenAuthentication]
    serializer_class = CartItemSerializer
    http_method_names = ["patch", "delete", "options"]

    def get_queryset(self):
        return CartItem.objects.filter(cart__public_id=self.kwargs["public_id"], cart__is_active=True)
