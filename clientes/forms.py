from django import forms

from .models import Cliente


class ClientePerfilForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = [
            "nombre_completo",
            "apellidos",
            "direccion",
            "ciudad",
            "codigo_postal",
            "provincia",
            "telefono",
            "metodo_pago_preferido",
        ]
        widgets = {
            "metodo_pago_preferido": forms.Select(),
        }
