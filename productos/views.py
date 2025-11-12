from django.shortcuts import render

from rest_framework import generics
from .models import Producto, Categoria
from .serializers import ProductoSerializer, CategoriaSerializer


class ProductoListView(generics.ListAPIView):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer


class CategoriaListView(generics.ListAPIView):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer


def home(request):
    return render(request, "productos/home.html")


def lista_productos(request):
    categoria_id = request.GET.get("categoria")

    categorias = Categoria.objects.all().order_by("nombre")

    productos = Producto.objects.all().select_related("categoria", "marca")

    categoria_seleccionada = None
    if categoria_id:
        try:
            categoria_seleccionada = Categoria.objects.get(id=categoria_id)
            productos = productos.filter(categoria=categoria_seleccionada)
        except Categoria.DoesNotExist:
            categoria_seleccionada = None  # si pasan un id raro, no filtramos

    context = {
        "productos": productos,
        "categorias": categorias,
        "categoria_seleccionada": categoria_seleccionada,
    }
    return render(request, "productos/lista_productos.html", context)
