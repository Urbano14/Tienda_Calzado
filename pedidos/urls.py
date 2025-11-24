from django.urls import path

from pedidos.api import PedidoCreateAPIView
from pedidos.checkout_views import (
    ConfirmacionCompraView,
    DetallesEntregaView,
    DetallesPagoView,
)

app_name = 'pedidos'

urlpatterns = [
    path('api/pedidos/', PedidoCreateAPIView.as_view(), name='api-pedidos-create'),
    path('checkout/entrega/', DetallesEntregaView.as_view(), name='checkout_entrega'),
    path('checkout/pago/', DetallesPagoView.as_view(), name='checkout_pago'),
    path('checkout/confirmacion/', ConfirmacionCompraView.as_view(), name='checkout_confirmacion'),
]
