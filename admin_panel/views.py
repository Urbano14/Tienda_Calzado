from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.views import LoginView, LogoutView
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator

from pedidos.models import Pedido
from productos.models import Producto
from .forms import (
    CategoriaForm,
    DepartamentoForm,
    MarcaForm,
    PedidoEstadoForm,
    ProductoForm,
    SeccionForm,
    TallaFormSet,
)


@method_decorator(staff_member_required(login_url="/panel/login/"), name="dispatch")
class PanelLogoutView(LogoutView):
    next_page = "/panel/login/"


class PanelLoginView(LoginView):
    template_name = "admin_panel/login.html"

    def get_success_url(self):
        return reverse("admin_panel:dashboard")


@staff_member_required(login_url="/panel/login/")
def dashboard(request):
    productos_total = Producto.objects.count()
    pedidos_pendientes = Pedido.objects.filter(estado=Pedido.Estados.PENDIENTE).count()
    pedidos_enviados = Pedido.objects.filter(estado=Pedido.Estados.ENVIADO).count()
    pedidos_entregados = Pedido.objects.filter(estado=Pedido.Estados.ENTREGADO).count()
    context = {
        "productos_total": productos_total,
        "pedidos_pendientes": pedidos_pendientes,
        "pedidos_enviados": pedidos_enviados,
        "pedidos_entregados": pedidos_entregados,
    }
    return render(request, "admin_panel/dashboard.html", context)


@staff_member_required(login_url="/panel/login/")
def productos_list(request):
    query = request.GET.get("q", "").strip()
    productos = Producto.objects.select_related("categoria", "marca").prefetch_related("tallas")
    if query:
        productos = productos.filter(nombre__icontains=query)
    productos = productos.order_by("-fecha_creacion")
    return render(
        request,
        "admin_panel/productos_list.html",
        {"productos": productos, "termino": query},
    )


@staff_member_required(login_url="/panel/login/")
@transaction.atomic
def producto_form(request, pk=None):
    producto = get_object_or_404(Producto, pk=pk) if pk else None

    if request.method == "POST":
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        talla_formset = TallaFormSet(request.POST, instance=producto)
        if form.is_valid() and talla_formset.is_valid():
            producto = form.save()
            talla_formset.instance = producto
            talla_formset.save()
            messages.success(request, "Producto guardado correctamente.")
            return redirect("admin_panel:productos_list")
        messages.error(request, "Revisa los campos marcados.")
    else:
        form = ProductoForm(instance=producto)
        talla_formset = TallaFormSet(instance=producto)

    return render(
        request,
        "admin_panel/producto_form.html",
        {
            "form": form,
            "talla_formset": talla_formset,
            "producto": producto,
        },
    )


@staff_member_required(login_url="/panel/login/")
def pedido_list(request):
    estado = request.GET.get("estado")
    pedidos = Pedido.objects.select_related("cliente").prefetch_related("items").order_by("-fecha_creacion")
    if estado:
        pedidos = pedidos.filter(estado=estado)
    estados = Pedido.Estados.choices
    return render(
        request,
        "admin_panel/pedidos_list.html",
        {"pedidos": pedidos, "estado": estado, "estados": estados},
    )


@staff_member_required(login_url="/panel/login/")
def pedido_detalle(request, pk):
    pedido = get_object_or_404(Pedido.objects.prefetch_related("items__producto"), pk=pk)
    if request.method == "POST":
        form = PedidoEstadoForm(request.POST, instance=pedido)
        if form.is_valid():
            form.save()
            messages.success(request, "Estado del pedido actualizado.")
            return redirect("admin_panel:pedido_detalle", pk=pedido.pk)
        messages.error(request, "No se pudo actualizar el estado.")
    else:
        form = PedidoEstadoForm(instance=pedido)

    return render(
        request,
        "admin_panel/pedido_detalle.html",
        {
            "pedido": pedido,
            "form": form,
        },
    )


@staff_member_required(login_url="/panel/login/")
def catalogo_formularios(request):
    dep_form = DepartamentoForm(prefix="dep")
    sec_form = SeccionForm(prefix="sec")
    cat_form = CategoriaForm(prefix="cat")
    marca_form = MarcaForm(prefix="mar")

    if request.method == "POST":
        if "dep-submit" in request.POST:
            dep_form = DepartamentoForm(request.POST, prefix="dep")
            if dep_form.is_valid():
                dep_form.save()
                messages.success(request, "Departamento creado.")
                return redirect("admin_panel:catalogo_formularios")
        elif "sec-submit" in request.POST:
            sec_form = SeccionForm(request.POST, prefix="sec")
            if sec_form.is_valid():
                sec_form.save()
                messages.success(request, "Sección creada.")
                return redirect("admin_panel:catalogo_formularios")
        elif "cat-submit" in request.POST:
            cat_form = CategoriaForm(request.POST, prefix="cat")
            if cat_form.is_valid():
                cat_form.save()
                messages.success(request, "Categoría creada.")
                return redirect("admin_panel:catalogo_formularios")
        elif "mar-submit" in request.POST:
            marca_form = MarcaForm(request.POST, request.FILES, prefix="mar")
            if marca_form.is_valid():
                marca_form.save()
                messages.success(request, "Marca creada.")
                return redirect("admin_panel:catalogo_formularios")
        messages.error(request, "Revisa los formularios con errores.")

    return render(
        request,
        "admin_panel/catalogo_formularios.html",
        {
            "dep_form": dep_form,
            "sec_form": sec_form,
            "cat_form": cat_form,
            "marca_form": marca_form,
        },
    )
