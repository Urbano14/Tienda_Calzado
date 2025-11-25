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
    pedido = get_object_or_404(
        Pedido.objects.prefetch_related("items", "items__producto"),
        numero_pedido=numero_pedido,
    )

    if pedido.cliente and pedido.cliente != request.user:
        raise PermissionDenied("No puedes ver este pedido.")

    contexto = {
        "pedido": pedido,
    }
    return render(request, "pedidos/detalle_pedido_publico.html", contexto)

