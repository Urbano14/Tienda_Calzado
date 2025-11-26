from django.contrib import admin
from django.urls import path, include, re_path

from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('productos.urls')),
    path('carrito/', include('carrito.urls')),
    path('clientes/', include('clientes.urls')),
    path('pedidos/', include('pedidos.urls')),
    path('api/', include('clientes.api_urls')),
    path('api/', include('pedidos.api_urls')),
]

# Servir MEDIA y archivos subidos por usuarios
# --------------------------------------------------------
# En local (DEBUG=True):
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# En producción (Render, DEBUG=False):
# Render NO sirve media automáticamente, así que usamos una vista estática explícita.
else:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]
