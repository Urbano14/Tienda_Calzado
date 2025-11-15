# carrito/utils.py

from .models import Carrito

def obtener_o_crear_carrito(request):
    """
    Busca un Carrito no completado asociado al guest_uuid en la cookie. 
    Si no existe o no hay cookie, crea un Carrito nuevo.
    """
    
    # Intentar obtener el UUID de la cookie
    guest_uuid = request.COOKIES.get('guest_carrito_id')
    carrito = None
    
    if guest_uuid:
        try:
            # 1. Buscar el carrito asociado al UUID
            carrito = Carrito.objects.get(guest_uuid=guest_uuid, completado=False)
        except Carrito.DoesNotExist:
            # Si el UUID es inválido o el carrito se completó/borró
            carrito = None
            
    if carrito is None:
        # 2. Si no se encontró, crear uno nuevo (el UUID se genera automáticamente)
        carrito = Carrito.objects.create()
        
    return carrito