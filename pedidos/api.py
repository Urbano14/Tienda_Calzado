from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from carrito.utils import obtener_o_crear_carrito
from pedidos.serializers import PedidoCreateSerializer, PedidoSerializer
from pedidos.services import crear_pedido_desde_carrito


class PedidoCreateAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = PedidoCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        datos_compra = serializer.validated_data.copy()
        datos_compra['carrito'] = obtener_o_crear_carrito(request)

        cliente = request.user if request.user.is_authenticated else None
        pedido = crear_pedido_desde_carrito(cliente, datos_compra)
        data = PedidoSerializer(pedido).data
        return Response(data, status=status.HTTP_201_CREATED)
