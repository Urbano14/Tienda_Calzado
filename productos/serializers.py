from rest_framework import serializers
from .models import Producto, Categoria, Marca, ImagenProducto, TallaProducto


class CategoriaSerializer(serializers.ModelSerializer):
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
