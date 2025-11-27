from django.urls import path

from .views import (
    PanelLoginView,
    PanelLogoutView,
    dashboard,
    productos_list,
    producto_form,
    pedido_list,
    pedido_detalle,
    catalogo_formularios,
)

app_name = "admin_panel"

urlpatterns = [
    path("login/", PanelLoginView.as_view(), name="login"),
    path("logout/", PanelLogoutView.as_view(), name="logout"),
    path("", dashboard, name="dashboard"),
    path("productos/", productos_list, name="productos_list"),
    path("productos/nuevo/", producto_form, name="producto_crear"),
    path("productos/<int:pk>/", producto_form, name="producto_editar"),
    path("pedidos/", pedido_list, name="pedidos_list"),
    path("pedidos/<int:pk>/", pedido_detalle, name="pedido_detalle"),
    path("catalogo/", catalogo_formularios, name="catalogo_formularios"),
]
