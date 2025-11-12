from django.urls import path
from productos.views import home, lista_productos, ProductoListView, CategoriaListView

urlpatterns = [
    path("", home, name="home"),
    path("productos/", lista_productos, name="lista-productos"),
    path("api/productos/", ProductoListView.as_view(), name="api-productos"),
    path("api/categorias/", CategoriaListView.as_view(), name="api-categorias"),
]
