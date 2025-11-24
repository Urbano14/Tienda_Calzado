from django.urls import path

from pedidos.api import PedidoCreateAPIView
from pedidos.checkout_views import (
    ConfirmacionCompraView,
    DetallesEntregaView,
    DetallesPagoView,
)
from pedidos.views import PedidoPublicDetailView, pedido_detalle_publico

app_name = 'pedidos'

urlpatterns = [
    path('api/pedidos/', PedidoCreateAPIView.as_view(), name='api-pedidos-create'),
    path('checkout/entrega/', DetallesEntregaView.as_view(), name='checkout_entrega'),
    path('checkout/pago/', DetallesPagoView.as_view(), name='checkout_pago'),
    path('checkout/confirmacion/', ConfirmacionCompraView.as_view(), name='checkout_confirmacion'),
    path('api/pedidos/<str:numero_pedido>/', PedidoPublicDetailView.as_view(), name="api-pedido-detalle"),
    path('pedidos/<str:numero_pedido>/', pedido_detalle_publico, name="api-pedido-detalle"),

]
