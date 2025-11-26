from django.urls import path

from .views import LoginView, RegistroView

urlpatterns = [
    path("registro/", RegistroView.as_view(), name="api-registro"),
    path("login/", LoginView.as_view(), name="api-login"),
]
