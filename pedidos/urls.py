from django.urls import path

from pedidos.api import PedidoCreateAPIView

app_name = 'pedidos'

urlpatterns = [
    path('api/pedidos/', PedidoCreateAPIView.as_view(), name='api-pedidos-create'),
]
