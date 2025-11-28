from django.urls import path

from .views import LoginView, RegistroView
from .views_perfil import perfil_cliente

urlpatterns = [
    path("registro/", RegistroView.as_view(), name="registro"),
    path("login/", LoginView.as_view(), name="login"),
    path("perfil/", perfil_cliente, name="perfil-cliente"),
]
