from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import ClientePerfilForm
from .models import Cliente


@login_required
def perfil_cliente(request):
    cliente, _ = Cliente.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = ClientePerfilForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            return redirect("home")
    else:
        form = ClientePerfilForm(instance=cliente)

    return render(request, "clientes/perfil_cliente.html", {"form": form})
