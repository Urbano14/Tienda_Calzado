from urllib import request
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from productos.models import Producto # Asumiendo que esta importación es correcta
from .models import ItemCarrito
from .utils import obtener_o_crear_carrito 
from django.db import IntegrityError # Importamos para manejar posibles errores de BD

# Create your views here.
# carrito/views.py

### Funciones de Ayuda (para manejar la cookie) ###

def _establecer_cookie_carrito(response, carrito):
    """Establece la cookie del carrito si no existe o ha cambiado."""
    # max_age = 30 días
    max_age = 3600 * 24 * 30 
    
    # Comprobamos si la cookie ya existe con el valor actual del carrito
    if request.COOKIES.get('guest_carrito_id') != str(carrito.guest_uuid):
        response.set_cookie('guest_carrito_id', str(carrito.guest_uuid), max_age=max_age)
    
    return response

### Vistas Principales ###

def ver_carrito(request):
    """Muestra el contenido actual del carrito."""
    
    # Obtiene o crea el carrito asociado al invitado/usuario
    carrito = obtener_o_crear_carrito(request)
    
    context = {
        'carrito': carrito, 
        'items': carrito.itemcarrito_set.all(),
        'total_articulos': carrito.obtener_total_articulos,
        'total_carrito': carrito.obtener_total_carrito,
    }
    
    # Renderiza la plantilla
    response = render(request, 'carrito/ver_carrito.html', context)
    
    # Asegura que la cookie se establezca si es un carrito nuevo
    return _establecer_cookie_carrito(response, carrito)


def agregar_producto(request, producto_id):
    """Añade una unidad de un producto al carrito, o incrementa la cantidad si ya existe."""
    
    # Solo permitimos POST para añadir productos
    if request.method != 'POST':
        return redirect('ver_carrito')
    
    producto = get_object_or_404(Producto, id=producto_id)
    cantidad = 1 # Puedes modificar esto para obtener la cantidad de un formulario POST

    carrito = obtener_o_crear_carrito(request)

    # get_or_create simplifica la lógica de buscar si ya existe
    item, creado = ItemCarrito.objects.get_or_create(
        carrito=carrito,
        producto=producto,
        defaults={'cantidad': cantidad}
    )
    
    if not creado:
        # Si el ítem ya existía, incrementamos la cantidad
        item.cantidad += cantidad
        item.save()

    # Redirecciona a la vista del carrito
    response = redirect('ver_carrito')
    
    # Asegura que la cookie se establezca si es un carrito nuevo
    return _establecer_cookie_carrito(response, carrito)


def eliminar_item(request, item_id):
    """Elimina una línea de ItemCarrito específica."""
    
    carrito = obtener_o_crear_carrito(request)
    
    # Buscamos el ítem asociado a este carrito y lo eliminamos
    item = get_object_or_404(ItemCarrito, id=item_id, carrito=carrito)
    item.delete()

    return redirect('ver_carrito')


def actualizar_item(request, item_id):
    """Actualiza la cantidad de un ítem. Asume que se envía la cantidad por POST."""
    
    if request.method == 'POST':
        try:
            # Captura la nueva cantidad (asegurando que es un entero positivo)
            nueva_cantidad = int(request.POST.get('cantidad', 0))
        except ValueError:
            return redirect('ver_carrito') # Ignorar si el valor no es un número
        
        carrito = obtener_o_crear_carrito(request)
        item = get_object_or_404(ItemCarrito, id=item_id, carrito=carrito)
        
        if nueva_cantidad > 0:
            item.cantidad = nueva_cantidad
            item.save()
        else:
            # Si la cantidad es cero o negativa, eliminamos el ítem
            item.delete()

    return redirect('ver_carrito')