from __future__ import annotations

import uuid
import logging
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Iterable, Optional, Tuple, Set

from django.conf import settings
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from carrito.models import Carrito
from pedidos.models import ItemPedido, Pedido
from pedidos.emails import enviar_confirmacion_pedido as enviar_correo_confirmacion
from productos.models import Producto, TallaProducto

TWOPLACES = Decimal('0.01')
User = get_user_model()
logger = logging.getLogger(__name__)


def generar_numero_pedido() -> str:
    """Genera un identificador unico basado en timestamp."""
    return timezone.now().strftime('%Y%m%d%H%M%S%f') + uuid.uuid4().hex[:6].upper()


def _as_decimal(value: Decimal | float | str) -> Decimal:
    return Decimal(value).quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def calcular_totales(items: Iterable[Dict], descuento: Decimal | None = None) -> Dict[str, Decimal]:
    subtotal = sum((item['total'] for item in items), Decimal('0'))
    subtotal = _as_decimal(subtotal)

    descuento = _as_decimal(descuento or Decimal('0'))
    if descuento > subtotal:
        descuento = subtotal

    iva = Decimal(str(getattr(settings, 'PEDIDOS_IVA', '0.21')))
    envio_gratis_desde = _as_decimal(getattr(settings, 'ENVIO_GRATIS_DESDE', Decimal('0')))
    coste_envio_estandar = _as_decimal(
        getattr(settings, 'COSTE_ENVIO_ESTANDAR', getattr(settings, 'PEDIDOS_COSTE_ENTREGA', Decimal('0')))
    )

    if subtotal >= envio_gratis_desde:
        coste_entrega = _as_decimal(Decimal('0'))
    else:
        coste_entrega = coste_envio_estandar

    base = subtotal - descuento
    impuestos = _as_decimal(base * iva)
    total = _as_decimal(subtotal + impuestos + coste_entrega - descuento)

    return {
        'subtotal': subtotal,
        'impuestos': impuestos,
        'coste_entrega': coste_entrega,
        'descuento': descuento,
        'total': total,
    }


def _resolver_carrito(usuario: Optional[User], datos: Dict) -> Carrito:
    carrito = datos.pop('carrito', None)
    if carrito:
        return carrito

    carrito_id = datos.get('carrito_id')
    queryset = Carrito.objects.all()

    if usuario:
        queryset = queryset.filter(usuario=usuario)
        if carrito_id:
            queryset = queryset.filter(pk=carrito_id)
    else:
        if not carrito_id:
            raise ValidationError('Se requiere un carrito para completar la compra.')
        queryset = queryset.filter(pk=carrito_id, usuario__isnull=True)

    carrito = queryset.order_by('-fecha_actualizacion', '-fecha_creacion').first()
    if not carrito:
        raise ValidationError('No se encontro un carrito valido para procesar.')
    return carrito


def _obtener_talla_map(claves: Set[Tuple[int, str]]):
    if not claves:
        return {}
    producto_ids = {producto_id for producto_id, _ in claves}
    tallas = TallaProducto.objects.select_for_update().filter(
        producto_id__in=producto_ids,
        talla__in=[talla for _, talla in claves],
    )
    return {(talla.producto_id, talla.talla): talla for talla in tallas}


def crear_pedido_desde_carrito(usuario: Optional[User], datos_compra: Dict) -> Pedido:
    datos = datos_compra.copy()
    carrito = _resolver_carrito(usuario, datos)

    items_carrito = list(carrito.items.select_related('producto'))
    if not items_carrito:
        raise ValidationError('El carrito esta vacio.')

    descuento = datos.get('descuento') or Decimal('0')
    metodo_pago = datos['metodo_pago']
    metodo_entrega = datos.get('metodo_entrega') or Pedido.MetodosEntrega.ESTANDAR
    direccion_envio = datos['direccion_envio']
    telefono = datos['telefono']
    email_contacto = datos.get('email_contacto')
    if not email_contacto:
        datos_cliente = datos.get('datos_cliente') or {}
        email_contacto = datos_cliente.get('email')

    producto_ids = [item.producto_id for item in items_carrito]

    with transaction.atomic():
        productos = Producto.objects.select_for_update().filter(id__in=producto_ids)
        producto_map = {producto.id: producto for producto in productos}

        talla_keys = {
            (item.producto_id, (item.talla or '').strip())
            for item in items_carrito
            if (item.talla or '').strip()
        }
        talla_map = _obtener_talla_map(talla_keys)

        producto_cantidades = defaultdict(int)
        talla_cantidades = defaultdict(int)
        items_precio = []

        for item in items_carrito:
            talla = (item.talla or '').strip()
            producto = producto_map.get(item.producto_id)
            if not producto:
                raise ValidationError(f"Producto {item.producto_id} no disponible.")

            cantidad = item.cantidad
            if cantidad <= 0:
                raise ValidationError('La cantidad de un item no es valida.')

            talla_key = (item.producto_id, talla) if talla else None
            if talla_key and talla_key in talla_map:
                disponible = talla_map[talla_key].stock
            else:
                disponible = producto.stock

            if cantidad > disponible:
                etiqueta = f" (talla {talla})" if talla else ''
                raise ValidationError(
                    f"Stock insuficiente para {producto.nombre}{etiqueta}. Disponible: {disponible}"
                )

            precio_unitario = producto.precio_oferta or producto.precio
            precio_unitario = _as_decimal(precio_unitario)
            total_linea = _as_decimal(precio_unitario * cantidad)

            items_precio.append(
                {
                    'producto': producto,
                    'talla': talla,
                    'cantidad': cantidad,
                    'precio_unitario': precio_unitario,
                    'total': total_linea,
                }
            )

            if talla_key and talla_key in talla_map:
                talla_cantidades[talla_key] += cantidad
            else:
                producto_cantidades[item.producto_id] += cantidad

        totales = calcular_totales(items_precio, descuento)

        pedido = Pedido.objects.create(
            cliente=usuario if usuario and usuario.is_authenticated else None,
            numero_pedido=generar_numero_pedido(),
            estado=Pedido.Estados.PENDIENTE,
            subtotal=totales['subtotal'],
            impuestos=totales['impuestos'],
            coste_entrega=totales['coste_entrega'],
            descuento=totales['descuento'],
            total=totales['total'],
            metodo_pago=metodo_pago,
            metodo_entrega=metodo_entrega,
            direccion_envio=direccion_envio,
            email_contacto=email_contacto,
            telefono=telefono,
        )

        ItemPedido.objects.bulk_create(
            [
                ItemPedido(
                    pedido=pedido,
                    producto=item['producto'],
                    talla=item['talla'],
                    cantidad=item['cantidad'],
                    precio_unitario=item['precio_unitario'],
                    total=item['total'],
                )
                for item in items_precio
            ]
        )

        for producto_id, cantidad in producto_cantidades.items():
            producto = producto_map[producto_id]
            producto.stock -= cantidad
            producto.save()

        for (producto_id, talla), cantidad in talla_cantidades.items():
            talla_obj = talla_map.get((producto_id, talla))
            if talla_obj:
                talla_obj.stock -= cantidad
                talla_obj.save()

        carrito.items.all().delete()
        carrito.fecha_actualizacion = timezone.now()
        carrito.save(update_fields=['fecha_actualizacion'])

    pedido_refrescado = (
        Pedido.objects
        .select_related('cliente')
        .prefetch_related('items__producto')
        .get(pk=pedido.pk)
    )
    if pedido_refrescado.metodo_pago != Pedido.MetodosPago.TARJETA:
        disparar_confirmacion_pedido(pedido_refrescado)
    return pedido_refrescado


def _destinatario_correo(pedido: Pedido) -> Optional[str]:
    if pedido.email_contacto:
        return pedido.email_contacto
    if pedido.cliente and getattr(pedido.cliente, "email", ""):
        return pedido.cliente.email
    return None


def _notificar_confirmacion(pedido: Pedido) -> None:
    destinatario = _destinatario_correo(pedido)
    if not destinatario:
        logger.warning("Pedido %s sin email de contacto para notificar.", pedido.pk)
        return

    enviado = enviar_correo_confirmacion(pedido, destinatario)
    if not enviado:
        logger.warning("No se pudo enviar la confirmación del pedido %s.", pedido.pk)


def disparar_confirmacion_pedido(pedido: Pedido) -> None:
    _notificar_confirmacion(pedido)

