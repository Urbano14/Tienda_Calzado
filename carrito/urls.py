from django.urls import path

from . import views

urlpatterns = [
    path("", views.ver_carrito, name="carrito"),
    path("agregar/<int:producto_id>/", views.agregar_al_carrito, name="agregar-al-carrito"),
    path("eliminar/<int:item_id>/", views.eliminar_del_carrito, name="eliminar-del-carrito"),
    path("actualizar/<int:item_id>/", views.actualizar_cantidad, name="actualizar-cantidad"),
]
