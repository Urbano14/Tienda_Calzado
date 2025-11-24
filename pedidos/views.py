from django.shortcuts import render, get_object_or_404
from .models import Pedido
from .serializers import PedidoPublicSerializer
from rest_framework import generics, permissions

# Create your views here.

class PedidoPublicDetailView(generics.RetrieveAPIView):
    queryset = Pedido.objects.all().prefetch_related("items", "items__producto")
    serializer_class = PedidoPublicSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "numero_pedido"


def pedido_detalle_publico(request, numero_pedido):
    pedido = get_object_or_404(Pedido, numero_pedido=numero_pedido)
    contexto = {
        "pedido": pedido,
    }
    return render(request, "pedidos/detalle_pedido_publico.html", contexto)

