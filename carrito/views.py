from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from productos.models import Producto
from .models import ItemCarrito
from .utils import obtener_o_crear_carrito


def _es_peticion_ajax(request):
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def _responder_totales(carrito, extra=None):
    data = {
        "total_articulos": carrito.obtener_total_articulos,
        "total_carrito": float(carrito.obtener_total_carrito),
    }
    if extra:
        data.update(extra)
    return JsonResponse(data)


def ver_carrito(request):
    """Muestra el contenido del carrito actual."""
    carrito = obtener_o_crear_carrito(request)
    context = {
        "carrito": carrito,
        "items": carrito.items.select_related("producto"),
        "total_articulos": carrito.obtener_total_articulos,
        "total_carrito": carrito.obtener_total_carrito,
    }
    return render(request, "carrito/carrito_compra.html", context)


@require_POST
def agregar_al_carrito(request, producto_id):
    """Anade un producto al carrito o incrementa su cantidad."""
    producto = get_object_or_404(Producto, id=producto_id)
    talla = request.POST.get("talla") or None

    try:
        cantidad = int(request.POST.get("cantidad", 1))
    except (TypeError, ValueError):
        cantidad = 1

    if cantidad < 1:
        cantidad = 1

    carrito = obtener_o_crear_carrito(request)
    item, creado = ItemCarrito.objects.get_or_create(
        carrito=carrito,
        producto=producto,
        talla=talla,
        defaults={"cantidad": cantidad},
    )

    if not creado:
        item.cantidad += cantidad
        item.save()

    if _es_peticion_ajax(request):
        return _responder_totales(
            carrito,
            {"item_id": item.id, "cantidad": item.cantidad, "item_subtotal": float(item.obtener_subtotal)},
        )

    return redirect("carrito")


@require_POST
def eliminar_del_carrito(request, item_id):
    """Elimina una linea del carrito."""
    carrito = obtener_o_crear_carrito(request)
    item = get_object_or_404(ItemCarrito, id=item_id, carrito=carrito)
    item.delete()

    if _es_peticion_ajax(request):
        return _responder_totales(carrito, {"removed": True, "item_id": item_id})

    return redirect("carrito")


@require_POST
def actualizar_cantidad(request, item_id):
    """Actualiza la cantidad seleccionada de un item."""
    carrito = obtener_o_crear_carrito(request)
    item = get_object_or_404(ItemCarrito, id=item_id, carrito=carrito)

    try:
        nueva_cantidad = int(request.POST.get("cantidad", 0))
    except (TypeError, ValueError):
        return redirect("carrito")

    if nueva_cantidad > 0:
        item.cantidad = nueva_cantidad
        item.save()
        payload = {
            "item_id": item.id,
            "cantidad": item.cantidad,
            "item_subtotal": float(item.obtener_subtotal),
        }
    else:
        item.delete()
        payload = {"removed": True, "item_id": item_id}

    if _es_peticion_ajax(request):
        return _responder_totales(carrito, payload)

    return redirect("carrito")
