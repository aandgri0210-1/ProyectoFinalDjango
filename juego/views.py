from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db.models import F, Q, Count, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView, DeleteView, ListView, UpdateView, DetailView

from .forms import AddInventoryItemForm, PersonajeForm, UseConsumableForm
from .mixins import OwnerRequiredMixin, SetLastCharacterMixin
from .models import Inventario, Personaje, Objeto

class ListaPersonajesView(LoginRequiredMixin, ListView):
    model = Personaje
    template_name = "personajes/personaje_list.html"
    context_object_name = "personajes"

    def get_queryset(self):
        queryset = Personaje.objects.filter(usuario=self.request.user)
        queryset = queryset.annotate(total_items=Count('inventario_item'))
        
        search = self.request.GET.get('buscar')
        if search:
            queryset = queryset.filter(
                Q(nombre__icontains=search) | 
                Q(nivel__icontains=search) |
                Q(estado__icontains=search)
            )
        
        return queryset

class CrearPersonajeView(LoginRequiredMixin, CreateView):
    model = Personaje
    form_class = PersonajeForm
    template_name = "personajes/personaje_form.html"

    def get_success_url(self):
        return reverse("juego:personaje-lista")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["usuario"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        if form.cleaned_data.get("vida_actual") is None:
            form.instance.vida_actual = form.cleaned_data.get("salud_maxima")
        response = super().form_valid(form)

        self.request.session["ultimo_personaje_id"] = self.object.id
        return response

class DetallePersonajeView(LoginRequiredMixin, OwnerRequiredMixin, SetLastCharacterMixin, DetailView):
    model = Personaje
    template_name = "personajes/personaje_detail.html"
    context_object_name = "personaje"

    def get_queryset(self):
        return Personaje.objects.filter(usuario=self.request.user).prefetch_related(
            "inventario_items__objeto"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tema"] = self.request.COOKIES.get("theme", "claro")
        
        stats = self.object.inventario_items.aggregate(
            total_objetos=Count('id'),
            total_cantidad=Sum('cantidad'),
        )
        context['inventario_stats'] = stats
        
        return context


class EditarPersonajeView(LoginRequiredMixin, OwnerRequiredMixin, UpdateView):
    model = Personaje
    form_class = PersonajeForm
    template_name = "personajes/personaje_form.html"

    def get_success_url(self):
        return reverse("juego:personaje-lista")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["usuario"] = self.request.user
        return kwargs


class EliminarPersonajeView(LoginRequiredMixin, OwnerRequiredMixin, DeleteView):
    model = Personaje
    template_name = "personajes/personaje_confirm_delete.html"

    def get_success_url(self):
        return reverse("juego:personaje-lista")

@login_required
@require_http_methods(["GET"])
def ver_inventario(request, personaje_id):
    personaje = get_object_or_404(Personaje, id=personaje_id, usuario=request.user)
    items = personaje.inventario_items.select_related("objeto")
    objetos_disponibles = Objeto.objects.all()
    return render(request, "inventario/inventario.html", {
        "personaje": personaje,
        "items": items,
        "objetos_disponibles": objetos_disponibles,
    })

@login_required
@require_http_methods(["POST"])
def agregar_objeto_inventario(request, personaje_id):
    personaje = get_object_or_404(Personaje, id=personaje_id, usuario=request.user)
    form = AddInventoryItemForm(request.POST)

    if not form.is_valid():
        return JsonResponse({"success": False, "errors": form.errors}, status=400)

    objeto = form.cleaned_data["objeto"]
    cantidad = form.cleaned_data["cantidad"]

    inv_item, created = Inventario.objects.get_or_create(
        personaje=personaje,
        objeto=objeto,
        defaults={"cantidad": cantidad},
    )

    if not created:
        Inventario.objects.filter(id=inv_item.id).update(
            cantidad=F("cantidad") + cantidad
        )
        inv_item.refresh_from_db()

    return JsonResponse({"success": True, "cantidad": inv_item.cantidad})


@login_required
@require_http_methods(["POST"])
def usar_consumible(request, personaje_id):
    personaje = get_object_or_404(Personaje, id=personaje_id, usuario=request.user)
    form = UseConsumableForm(request.POST, personaje=personaje)

    if not form.is_valid():
        return JsonResponse({"success": False, "errors": form.errors}, status=400)

    inv_item = Inventario.objects.get(id=form.cleaned_data["inventario_item_id"])
    Inventario.objects.filter(id=inv_item.id).update(cantidad=F("cantidad") - 1)
    inv_item.refresh_from_db()

    if inv_item.cantidad <= 0:
        inv_item.delete()

    return JsonResponse({"success": True})

@login_required
@require_http_methods(["POST"])
def fijar_tema(request, personaje_id):
    tema = request.GET.get("theme", "claro")
    if tema not in ["claro", "oscuro"]:
        tema = "claro"

    response = redirect("juego:personaje-detalle", pk=personaje_id)
    response.set_cookie(
        key="theme",
        value=tema,
        max_age=365 * 24 * 60 * 60,
        httponly=True,
        secure=False,
    )
    return response

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('juego:personaje-lista')
        else:
            error = 'Usuario o contraseña incorrectos'
            return render(request, 'inicio-sesion.html', {'error': error})
    
    return render(request, 'inicio-sesion.html')

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        
        if User.objects.filter(username=username).exists():
            error = 'El usuario ya existe'
            return render(request, 'registro.html', {'error': error})
        
        if password != password_confirm:
            error = 'Las contraseñas no coinciden'
            return render(request, 'registro.html', {'error': error})
        
        if len(password) < 6:
            error = 'La contraseña debe tener al menos 6 caracteres'
            return render(request, 'register.html', {'error': error})
        
        user = User.objects.create_user(username=username, password=password)
        login(request, user)
        return redirect('juego:personaje-lista')
    
    return render(request, 'registro.html')

def logout_view(request):
    logout(request)
    return redirect('juego:inicio-sesion')
