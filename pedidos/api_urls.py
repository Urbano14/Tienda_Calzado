from django.urls import path

from pedidos.api import PedidoCreateAPIView
from pedidos.views import PedidoPublicDetailView

urlpatterns = [
    path("pedidos/", PedidoCreateAPIView.as_view(), name="api-pedidos-create"),
    path("pedidos/<str:numero_pedido>/", PedidoPublicDetailView.as_view(), name="api-pedido-detalle"),
]
