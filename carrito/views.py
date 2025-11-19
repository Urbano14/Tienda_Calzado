from django.contrib import messages
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


def _stock_disponible(producto, talla=None):
    """Devuelve el stock disponible: primero el de la talla (si existe), si no el general."""
    if talla:
        talla_obj = producto.tallas.filter(talla=talla).first()
        if talla_obj:
            return talla_obj.stock
    return producto.stock


def _ajustar_stock(producto, talla, delta):
    """
    Ajusta stock cuando el carrito consume o devuelve unidades.
    delta negativo reduce stock, delta positivo lo devuelve.
    """
    if talla:
        talla_obj = producto.tallas.filter(talla=talla).first()
        if talla_obj:
            talla_obj.stock = max(talla_obj.stock + delta, 0)
            talla_obj.save()
        return

    producto.stock = max(producto.stock + delta, 0)
    producto.save()


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
    item = ItemCarrito.objects.filter(
        carrito=carrito,
        producto=producto,
        talla=talla,
    ).first()

    stock_disponible = _stock_disponible(producto, talla)
    cantidad_actual = item.cantidad if item else 0
    nueva_cantidad = cantidad_actual + cantidad

    if stock_disponible <= 0:
        mensaje = "No hay más stock de este producto."
        if _es_peticion_ajax(request):
            return JsonResponse({"error": mensaje, "stock_disponible": 0}, status=400)
        messages.error(request, mensaje)
        return redirect("detalle-producto", pk=producto.id)

    if nueva_cantidad > stock_disponible:
        mensaje = "No hay más stock de este producto."
        if _es_peticion_ajax(request):
            return _responder_totales(
                carrito,
                {
                    "warning": mensaje,
                    "stock_disponible": stock_disponible,
                },
            )
        messages.error(request, mensaje)
        return redirect("detalle-producto", pk=producto.id)

    delta = nueva_cantidad - cantidad_actual

    if item:
        item.cantidad = nueva_cantidad
        item.save()
    else:
        item = ItemCarrito.objects.create(
            carrito=carrito,
            producto=producto,
            talla=talla,
            cantidad=nueva_cantidad,
        )

    if delta:
        _ajustar_stock(producto, talla, -delta)

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
    _ajustar_stock(item.producto, item.talla, item.cantidad)
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
        stock_disponible = _stock_disponible(item.producto, item.talla)
        cantidad_actual = item.cantidad
        delta = nueva_cantidad - cantidad_actual
        mensaje = None

        if delta > 0 and delta > stock_disponible:
            delta = stock_disponible
            nueva_cantidad = cantidad_actual + delta
            mensaje = f"Cantidad ajustada a {nueva_cantidad} por disponibilidad de stock."
            messages.warning(request, mensaje)

        if delta != 0:
            _ajustar_stock(item.producto, item.talla, -delta)

        item.cantidad = nueva_cantidad
        item.save()
        payload = {
            "item_id": item.id,
            "cantidad": item.cantidad,
            "item_subtotal": float(item.obtener_subtotal),
        }
        if mensaje:
            payload["warning"] = mensaje
    else:
        item.delete()
        payload = {"removed": True, "item_id": item_id}

    if _es_peticion_ajax(request):
        return _responder_totales(carrito, payload)

    return redirect("carrito")
