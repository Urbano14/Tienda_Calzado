from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from decimal import Decimal


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('productos', '0002_tallaproducto'),
    ]

    operations = [
        migrations.CreateModel(
            name='Pedido',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('numero_pedido', models.CharField(max_length=30, unique=True)),
                ('estado', models.CharField(choices=[('pendiente', 'Pendiente'), ('preparando', 'Preparando'), ('enviado', 'Enviado'), ('entregado', 'Entregado'), ('cancelado', 'Cancelado')], default='pendiente', max_length=20)),
                ('subtotal', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=12)),
                ('impuestos', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=12)),
                ('coste_entrega', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=12)),
                ('descuento', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=12)),
                ('total', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=12)),
                ('metodo_pago', models.CharField(choices=[('tarjeta', 'Tarjeta'), ('transferencia', 'Transferencia'), ('paypal', 'PayPal'), ('contrareembolso', 'Contrareembolso')], max_length=30)),
                ('direccion_envio', models.TextField()),
                ('telefono', models.CharField(max_length=30)),
                ('cliente', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pedidos', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-fecha_creacion',),
            },
        ),
        migrations.CreateModel(
            name='ItemPedido',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('talla', models.CharField(blank=True, max_length=20)),
                ('cantidad', models.PositiveIntegerField()),
                ('precio_unitario', models.DecimalField(decimal_places=2, max_digits=12)),
                ('total', models.DecimalField(decimal_places=2, max_digits=12)),
                ('pedido', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='pedidos.pedido')),
                ('producto', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='items_pedido', to='productos.producto')),
            ],
        ),
    ]
