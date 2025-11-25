from urllib.parse import urlencode

from django.db.models import Prefetch, Q
from django.shortcuts import render, get_object_or_404

from rest_framework import generics

from .models import Categoria, Departamento, Marca, Producto, Seccion
from .serializers import CategoriaSerializer, ProductoSerializer


def _resolve_by_slug_or_pk(model, raw_value):
    if not raw_value:
        return None

    candidate = model.objects.filter(slug__iexact=raw_value).first()
    if candidate:
        return candidate

    if str(raw_value).isdigit():
        return model.objects.filter(pk=raw_value).first()

    return None


def apply_catalog_filters(queryset, filtros):
    context = {
        "departamento": None,
        "seccion": None,
        "categoria": None,
        "marca": None,
    }

    categoria = _resolve_by_slug_or_pk(Categoria, filtros.get("categoria"))
    if categoria:
        queryset = queryset.filter(categoria=categoria)
        context["categoria"] = categoria
        if categoria.seccion:
            context["seccion"] = categoria.seccion
            if categoria.seccion.departamento:
                context["departamento"] = categoria.seccion.departamento

    seccion = _resolve_by_slug_or_pk(Seccion, filtros.get("seccion"))
    if seccion and not context["seccion"]:
        queryset = queryset.filter(categoria__seccion=seccion)
        context["seccion"] = seccion
        context["departamento"] = seccion.departamento

    departamento = _resolve_by_slug_or_pk(Departamento, filtros.get("departamento"))
    if departamento and not context["departamento"]:
        queryset = queryset.filter(categoria__seccion__departamento=departamento)
        context["departamento"] = departamento

    marca = filtros.get("fabricante") or filtros.get("marca")
    marca_obj = _resolve_by_slug_or_pk(Marca, marca)
    if marca_obj:
        queryset = queryset.filter(marca=marca_obj)
        context["marca"] = marca_obj

    return queryset, context


def _build_querystring(base_params, path, **updates):
    params = {k: v for k, v in base_params.items() if v}
    for key, value in updates.items():
        if value is None:
            params.pop(key, None)
        else:
            params[key] = value

    query = urlencode(params)
    return f"{path}?{query}" if query else path


class ProductoListView(generics.ListAPIView):
    queryset = Producto.objects.select_related(
        "categoria",
        "categoria__seccion",
        "categoria__seccion__departamento",
        "marca",
    )
    serializer_class = ProductoSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        filtros = {
            "departamento": self.request.query_params.get("departamento"),
            "seccion": self.request.query_params.get("seccion"),
            "categoria": self.request.query_params.get("categoria"),
            "fabricante": self.request.query_params.get("fabricante")
            or self.request.query_params.get("marca"),
        }

        queryset, _ = apply_catalog_filters(queryset, filtros)

        termino = (
            self.request.query_params.get("nombre")
            or self.request.query_params.get("titulo")
            or self.request.query_params.get("q")
        )
        if termino:
            termino = termino.strip()
            search_filter = Q(nombre__icontains=termino)
            search_filter |= Q(categoria__nombre__icontains=termino)
            search_filter |= Q(categoria__seccion__nombre__icontains=termino)
            search_filter |= Q(categoria__seccion__departamento__nombre__icontains=termino)
            search_filter |= Q(marca__nombre__icontains=termino)
            queryset = queryset.filter(search_filter)

        return queryset


class ProductoDetailView(generics.RetrieveAPIView):
    queryset = Producto.objects.select_related("categoria", "categoria__seccion__departamento", "marca")
    serializer_class = ProductoSerializer


class CategoriaListView(generics.ListAPIView):
    queryset = Categoria.objects.select_related("seccion", "seccion__departamento")
    serializer_class = CategoriaSerializer


def home(request):
    categorias_destacadas = (
        Categoria.objects.select_related("seccion", "seccion__departamento")
        .order_by(
            "seccion__departamento__orden",
            "seccion__orden",
            "nombre",
        )[:4]
    )

    context = {
        "categorias_destacadas": categorias_destacadas,
    }
    return render(request, "pagina_inicio.html", context)


def lista_productos(request):
    filtros = {
        "departamento": request.GET.get("departamento"),
        "seccion": request.GET.get("seccion"),
        "categoria": request.GET.get("categoria"),
        "fabricante": request.GET.get("fabricante"),
    }

    productos = (
        Producto.objects.select_related(
            "categoria",
            "categoria__seccion",
            "categoria__seccion__departamento",
            "marca",
        ).prefetch_related("imagenes")
    )

    productos, filtros_contexto = apply_catalog_filters(productos, filtros)

    categorias = Categoria.objects.select_related(
        "seccion",
        "seccion__departamento",
    ).order_by("seccion__departamento__orden", "seccion__orden", "nombre")

    departamentos = (
        Departamento.objects.prefetch_related(
            Prefetch(
                "secciones",
                queryset=Seccion.objects.prefetch_related("categorias").order_by("orden", "nombre"),
            )
        )
        .order_by("orden", "nombre")
        .all()
    )

    marcas = Marca.objects.order_by("nombre").all()

    active_params = {k: v for k, v in filtros.items() if v}

    breadcrumb = []
    if filtros_contexto["departamento"]:
        breadcrumb.append(
            {
                "label": filtros_contexto["departamento"].nombre,
                "url": _build_querystring(active_params, request.path, departamento=filtros_contexto["departamento"].slug, seccion=None, categoria=None),
            }
        )
    if filtros_contexto["seccion"]:
        breadcrumb.append(
            {
                "label": filtros_contexto["seccion"].nombre,
                "url": _build_querystring(active_params, request.path, seccion=filtros_contexto["seccion"].slug, categoria=None),
            }
        )
    if filtros_contexto["categoria"]:
        breadcrumb.append(
            {
                "label": filtros_contexto["categoria"].nombre,
                "url": _build_querystring(active_params, request.path, categoria=filtros_contexto["categoria"].slug),
            }
        )
    if filtros_contexto["marca"]:
        breadcrumb.append(
            {
                "label": filtros_contexto["marca"].nombre,
                "url": _build_querystring(active_params, request.path, fabricante=filtros_contexto["marca"].slug),
            }
        )

    chips = []
    if filtros_contexto["departamento"]:
        chips.append(
            {
                "label": filtros_contexto["departamento"].nombre,
                "url": _build_querystring(active_params, request.path, departamento=None, seccion=None, categoria=None),
            }
        )
    if filtros_contexto["seccion"]:
        chips.append(
            {
                "label": filtros_contexto["seccion"].nombre,
                "url": _build_querystring(active_params, request.path, seccion=None, categoria=None),
            }
        )
    if filtros_contexto["categoria"]:
        chips.append(
            {
                "label": filtros_contexto["categoria"].nombre,
                "url": _build_querystring(active_params, request.path, categoria=None),
            }
        )
    if filtros_contexto["marca"]:
        chips.append(
            {
                "label": filtros_contexto["marca"].nombre,
                "url": _build_querystring(active_params, request.path, fabricante=None),
            }
        )

    context = {
        "productos": productos,
        "categorias": categorias,
        "departamentos": departamentos,
        "marcas": marcas,
        "filtros": filtros,
        "breadcrumb": breadcrumb,
        "chips": chips,
        "filtros_contexto": filtros_contexto,
        "active_params": active_params,
        "base_path": request.path,
    }
    return render(request, "productos/lista_productos.html", context)


def detalle_producto(request, pk):
    producto = get_object_or_404(
        Producto.objects.select_related("categoria", "marca").prefetch_related(
            "imagenes", "tallas"
        ),
        pk=pk,
    )

    imagen_principal = producto.imagen_destacada

    context = {
        "producto": producto,
        "imagen_principal": imagen_principal,
        "tallas": producto.tallas.all(),
    }
    return render(request, "productos/detalle_producto.html", context)
