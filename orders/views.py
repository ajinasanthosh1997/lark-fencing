from rest_framework import generics
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import NotFound

from .models import Order, ReturnEvidence, ReturnRequest
from .serializers import (
    OrderCreateSerializer,
    ReturnEvidenceCreateSerializer,
    ReturnRequestCreateSerializer,
)


class OrderCreate(generics.CreateAPIView):
    authentication_classes = [TokenAuthentication]
    queryset = Order.objects.all()
    serializer_class = OrderCreateSerializer


class OrderDetail(generics.RetrieveAPIView):
    authentication_classes = [TokenAuthentication]
    queryset = Order.objects.prefetch_related("items", "payments")
    serializer_class = OrderCreateSerializer
    lookup_field = "public_id"

    def get_object(self):
        email = self.request.query_params.get("email", "").strip()
        if not email:
            raise NotFound("Order details could not be verified.")
        try:
            return self.get_queryset().get(
                public_id=self.kwargs["public_id"], email__iexact=email
            )
        except Order.DoesNotExist as exc:
            raise NotFound("Order details could not be verified.") from exc


class ReturnRequestCreate(generics.CreateAPIView):
    authentication_classes = [TokenAuthentication]
    queryset = ReturnRequest.objects.all()
    serializer_class = ReturnRequestCreateSerializer


class ReturnEvidenceCreate(generics.CreateAPIView):
    authentication_classes = [TokenAuthentication]
    queryset = ReturnEvidence.objects.all()
    serializer_class = ReturnEvidenceCreateSerializer
