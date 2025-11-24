from rest_framework import serializers
from .models import (
    Categoria,
    Departamento,
    ImagenProducto,
    Marca,
    Producto,
    Seccion,
    TallaProducto,
)


class DepartamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Departamento
        fields = "__all__"


class SeccionSerializer(serializers.ModelSerializer):
    departamento = DepartamentoSerializer(read_only=True)

    class Meta:
        model = Seccion
        fields = "__all__"


class CategoriaSerializer(serializers.ModelSerializer):
    seccion = SeccionSerializer(read_only=True)

    class Meta:
        model = Categoria
        fields = "__all__"


class MarcaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marca
        fields = "__all__"


class ImagenProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImagenProducto
        fields = "__all__"


class TallaProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TallaProducto
        fields = "__all__"


class ProductoSerializer(serializers.ModelSerializer):
    categoria = CategoriaSerializer(read_only=True)
    marca = MarcaSerializer(read_only=True)
    imagenes = ImagenProductoSerializer(many=True, read_only=True)
    tallas = TallaProductoSerializer(many=True, read_only=True)

    class Meta:
        model = Producto
        fields = "__all__"
