from django.urls import path
from productos.views import (
    home,
    lista_productos,
    detalle_producto,
    ProductoListView,
    ProductoDetailView,
    CategoriaListView,
)

urlpatterns = [
    path("", home, name="home"),
    path("productos/", lista_productos, name="lista-productos"),
    path("productos/<int:pk>/", detalle_producto, name="detalle-producto"),
    path("api/productos/", ProductoListView.as_view(), name="api-productos"),
    path(
        "api/productos/<int:pk>/",
        ProductoDetailView.as_view(),
        name="api-producto-detalle",
    ),
    path("api/categorias/", CategoriaListView.as_view(), name="api-categorias"),
]
