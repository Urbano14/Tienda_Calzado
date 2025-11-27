from django import forms
from django.forms import inlineformset_factory

from productos.models import (
    Categoria,
    Marca,
    Producto,
    Seccion,
    Departamento,
    TallaProducto,
    ImagenProducto,
)
from pedidos.models import Pedido


class ProductoForm(forms.ModelForm):
    main_image = forms.ImageField(
        label="Imagen principal",
        required=False,
        help_text="Se sustituye la imagen existente si ya hay una.",
    )

    class Meta:
        model = Producto
        fields = [
            "nombre",
            "descripcion",
            "precio",
            "precio_oferta",
            "marca",
            "categoria",
            "genero",
            "color",
            "material",
            "stock",
            "es_destacado",
        ]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 3}),
        }

    def save(self, commit=True):
        producto = super().save(commit=commit)
        imagen = self.cleaned_data.get("main_image")
        if imagen:
            principal = producto.imagenes.first()
            if principal:
                principal.imagen = imagen
                principal.save()
            else:
                ImagenProducto.objects.create(producto=producto, imagen=imagen, es_principal=True)
        return producto


TallaFormSet = inlineformset_factory(
    Producto,
    TallaProducto,
    fields=["talla", "stock"],
    extra=1,
    can_delete=True,
)


class DepartamentoForm(forms.ModelForm):
    class Meta:
        model = Departamento
        fields = ["nombre", "descripcion", "orden"]


class SeccionForm(forms.ModelForm):
    class Meta:
        model = Seccion
        fields = ["departamento", "nombre", "descripcion", "orden"]


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ["seccion", "nombre", "descripcion"]


class MarcaForm(forms.ModelForm):
    class Meta:
        model = Marca
        fields = ["nombre", "imagen"]


class PedidoEstadoForm(forms.ModelForm):
    class Meta:
        model = Pedido
        fields = ["estado"]
