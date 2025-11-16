# carrito/utils.py

from .models import Carrito


def obtener_o_crear_carrito(request):
    """Devuelve el carrito del usuario autenticado o el asociado a la sesión actual."""

    if request.user.is_authenticated:
        carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
        request.session.pop('guest_carrito_id', None)
        return carrito

    carrito_id = request.session.get('guest_carrito_id')

    if carrito_id:
        carrito = Carrito.objects.filter(id=carrito_id, usuario__isnull=True).first()
        if carrito:
            return carrito

    carrito = Carrito.objects.create()
    request.session['guest_carrito_id'] = carrito.id
    return carrito