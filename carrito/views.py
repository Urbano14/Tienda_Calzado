from django.shortcuts import render, redirect, get_object_or_404
from productos.models import Producto  # Asumiendo que esta importación es correcta
from .models import ItemCarrito
from .utils import obtener_o_crear_carrito 

# Create your views here.
# carrito/views.py

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
    
    return render(request, 'carrito/ver_carrito.html', context)


def agregar_producto(request, producto_id):
    """Añade una unidad de un producto al carrito, o incrementa la cantidad si ya existe."""
    
    # Solo permitimos POST para añadir productos
    if request.method != 'POST':
        return redirect('ver_carrito')
    
    producto = get_object_or_404(Producto, id=producto_id)
    talla = request.POST.get('talla') or None
    try:
        cantidad = int(request.POST.get('cantidad', 1))
    except (TypeError, ValueError):
        cantidad = 1

    if cantidad < 1:
        cantidad = 1

    carrito = obtener_o_crear_carrito(request)

    # get_or_create simplifica la lógica de buscar si ya existe
    item, creado = ItemCarrito.objects.get_or_create(
        carrito=carrito,
        producto=producto,
        talla=talla,
        defaults={'cantidad': cantidad}
    )
    
    if not creado:
        # Si el ítem ya existía, incrementamos la cantidad
        item.cantidad += cantidad
        item.save()

    return redirect('ver_carrito')


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