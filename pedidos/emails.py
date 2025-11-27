from __future__ import annotations

import logging
from typing import Optional

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from pedidos.models import Pedido

logger = logging.getLogger(__name__)


def _nombre_cliente(pedido: Pedido) -> str:
    if pedido.cliente:
        posibles = (
            getattr(pedido.cliente, "first_name", ""),
            getattr(pedido.cliente, "last_name", ""),
            getattr(pedido.cliente, "nombre", ""),
            getattr(pedido.cliente, "apellidos", ""),
        )
        for valor in posibles:
            if valor:
                return valor
    return ""


def _build_context(pedido: Pedido, destinatario: str) -> dict:
    return {
        "pedido": pedido,
        "items": pedido.items.all(),
        "nombre_cliente": _nombre_cliente(pedido),
        "destinatario": destinatario,
        "metodo_pago": pedido.get_metodo_pago_display() if hasattr(pedido, "get_metodo_pago_display") else pedido.metodo_pago,
        "direccion_envio": pedido.direccion_envio,
        "total": pedido.total,
        "tracking_token": str(pedido.tracking_token),
    }


def enviar_confirmacion_pedido(pedido: Pedido, destinatario: Optional[str]) -> bool:
    """
    Genera y envía un correo HTML con el resumen del pedido.
    Devuelve True si se envió el correo y False si faltaban datos.
    """
    email = (destinatario or "").strip()
    if not email:
        return False

    context = _build_context(pedido, email)
    html_body = render_to_string("pedidos/emails/confirmacion_pedido.html", context)
    text_body = strip_tags(html_body)

    subject = f"Pedido {pedido.numero_pedido} recibido"
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or None
    message = EmailMultiAlternatives(subject, text_body, from_email, [email])
    message.attach_alternative(html_body, "text/html")
    try:
        message.send()
        return True
    except Exception:  # pragma: no cover - logged for diagnosis, flow must continue
        logger.exception("Error enviando email de confirmación de pedido %s", pedido.pk)
        return False
