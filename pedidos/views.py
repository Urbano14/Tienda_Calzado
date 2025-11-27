import uuid

from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404
from rest_framework import generics, permissions
from rest_framework.exceptions import NotFound, PermissionDenied as DRFPermissionDenied

from .models import Pedido
from .serializers import PedidoPublicSerializer

# Create your views here.


class PedidoPublicDetailView(generics.RetrieveAPIView):
    queryset = Pedido.objects.all().prefetch_related("items", "items__producto")
    serializer_class = PedidoPublicSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "numero_pedido"

    def get_object(self):
        numero = self.kwargs.get(self.lookup_field)
        try:
            pedido = self.get_queryset().get(numero_pedido=numero)
        except Pedido.DoesNotExist as exc:
            raise NotFound("Pedido no encontrado") from exc

        if pedido.cliente and pedido.cliente != self.request.user:
            raise DRFPermissionDenied("Ese pedido pertenece a otra cuenta.")

        return pedido


def pedido_detalle_publico(request, numero_pedido):
    pedido = (
        Pedido.objects.prefetch_related("items", "items__producto")
        .filter(numero_pedido=numero_pedido)
        .first()
    )

    if not pedido:
        return render(
            request,
            "pedidos/detalle_pedido_publico.html",
            {"pedido": None, "mensaje_error": "No encontramos ese pedido."},
            status=404,
        )

    if pedido.cliente and pedido.cliente != request.user:
        raise PermissionDenied("No puedes ver este pedido.")

    contexto = {
        "pedido": pedido,
    }
    return render(request, "pedidos/detalle_pedido_publico.html", contexto)


def _mask_phone(phone: str) -> str:
    raw = (phone or "").strip()
    if not raw:
        return ""
    digits = "".join(ch for ch in raw if ch.isdigit())
    if len(digits) <= 4:
        masked = "*" * len(digits)
    else:
        masked = "*" * (len(digits) - 4) + digits[-4:]
    return masked


def seguimiento_pedido(request, tracking_token):
    try:
        token_uuid = uuid.UUID(str(tracking_token))
    except (ValueError, TypeError):
        pedido = None
    else:
        pedido = (
            Pedido.objects.prefetch_related("items__producto")
            .filter(tracking_token=token_uuid)
            .first()
        )

    if not pedido:
        return render(
            request,
            "pedido/seguimiento.html",
            {"pedido": None, "masked_phone": ""},
            status=404,
        )
    context = {
        "pedido": pedido,
        "masked_phone": _mask_phone(pedido.telefono),
    }
    return render(request, "pedido/seguimiento.html", context)

