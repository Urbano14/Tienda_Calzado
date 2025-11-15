from django.urls import path
from . import views
urlpatterns = [
    # Ruta: /carrito/ (Muestra el contenido del carrito)
    path('', views.ver_carrito, name='ver_carrito'),
    
    # Ruta: /carrito/agregar/<id_producto>/ (Añade un producto al carrito)
    # El <int:producto_id> captura el ID del producto de la URL
    path('agregar/<int:producto_id>/', views.agregar_producto, name='agregar_producto'),
    
    # Ruta: /carrito/eliminar/<id_item>/ (Elimina una línea de ItemCarrito)
    path('eliminar/<int:item_id>/', views.eliminar_item, name='eliminar_item'),
    
    # Ruta: /carrito/actualizar/<id_item>/ (Para cambiar la cantidad de un ítem)
    path('actualizar/<int:item_id>/', views.actualizar_item, name='actualizar_item'),
]