from django.core.exceptions import PermissionDenied
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Avg, Count, F, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView, DeleteView, ListView, UpdateView, DetailView, View

from .forms import AddInventoryItemForm, CombateForm, EnemigoForm, IniciarCombateForm, PersonajeForm, SeleccionarEnemigoForm, UseConsumableForm, ZonaForm
from .mixins import AdminRequiredMixin, OwnerRequiredMixin, SetLastCharacterMixin
from .models import Enemigo, Inventario, Objeto, Personaje, Zona, Combate


def inicio_redirect_view(request):
    if request.user.is_authenticated:
        return redirect('juego:personaje-lista')
    return redirect('juego:inicio-sesion')

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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Verificar si el usuario es administrador
        es_admin = self.request.user.groups.filter(
            name__in=['GAME_MASTER', 'ADMIN_CONTENIDO', 'ADMIN']
        ).exists() or self.request.user.is_staff or self.request.user.is_superuser
        
        context['es_admin'] = es_admin
        
        return context

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
        
        # Asignar estadísticas base automáticamente
        form.instance.exp_actual = 0
        form.instance.ataque = 10
        form.instance.defensa = 10
        form.instance.salud_maxima = 50
        form.instance.vida_actual = 50
        form.instance.velocidad = 10
        
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
        context["tema"] = self.request.COOKIES.get("theme") or self.request.COOKIES.get("tema_preferido", "claro")
        
        stats = self.object.inventario_items.aggregate(
            total_objetos=Count('id'),
            total_cantidad=Sum('cantidad'),
        )
        context['inventario_stats'] = stats
        
        # Agregar información de experiencia del nivel
        exp_minima, exp_maxima = self.object.obtener_exp_requerida_nivel_actual()
        progreso = self.object.obtener_progreso_nivel()
        context['exp_minima'] = exp_minima
        context['exp_maxima'] = exp_maxima
        context['exp_progreso'] = progreso
        context['exp_rango_actual'] = f"{exp_minima}/{exp_maxima}"

        bonus_stats = self.object.inventario_items.filter(equipado=True).aggregate(
            bonus_ataque=Sum("objeto__bonus_ataque"),
            bonus_defensa=Sum("objeto__bonus_defensa"),
            bonus_salud=Sum("objeto__bonus_salud"),
            bonus_velocidad=Sum("objeto__bonus_velocidad"),
        )

        context['bonus_ataque'] = bonus_stats.get('bonus_ataque') or 0
        context['bonus_defensa'] = bonus_stats.get('bonus_defensa') or 0
        context['bonus_salud'] = bonus_stats.get('bonus_salud') or 0
        context['bonus_velocidad'] = bonus_stats.get('bonus_velocidad') or 0

        context['ataque_total'] = self.object.ataque + context['bonus_ataque']
        context['defensa_total'] = self.object.defensa + context['bonus_defensa']
        context['salud_maxima_total'] = self.object.salud_maxima + context['bonus_salud']
        context['velocidad_total'] = self.object.velocidad + context['bonus_velocidad']

        context['objetos_equipados'] = self.object.inventario_items.filter(
            equipado=True
        ).select_related('objeto')
        
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
        
        # Verificar si el usuario es administrador
        es_admin = self.request.user.groups.filter(
            name__in=['GAME_MASTER', 'ADMIN_CONTENIDO', 'ADMIN']
        ).exists() or self.request.user.is_staff or self.request.user.is_superuser
        
        # Solo admins pueden editar
        kwargs["es_editable"] = es_admin
        
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Verificar si el usuario es administrador
        es_admin = self.request.user.groups.filter(
            name__in=['GAME_MASTER', 'ADMIN_CONTENIDO', 'ADMIN']
        ).exists() or self.request.user.is_staff or self.request.user.is_superuser
        
        context['es_editable'] = es_admin
        
        return context


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
@require_http_methods(["GET"])
def detalle_objeto_inventario(request, personaje_id, inventario_item_id):
    personaje = get_object_or_404(Personaje, id=personaje_id, usuario=request.user)
    item = get_object_or_404(
        Inventario.objects.select_related("objeto"),
        id=inventario_item_id,
        personaje=personaje,
    )

    return render(request, "inventario/objeto_detalle.html", {
        "personaje": personaje,
        "item": item,
        "objeto": item.objeto,
    })

@login_required
@require_http_methods(["POST"])
def agregar_objeto_inventario(request, personaje_id):
    personaje = get_object_or_404(Personaje, id=personaje_id, usuario=request.user)
    form = AddInventoryItemForm(request.POST)
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"

    if not form.is_valid():
        if is_ajax:
            return JsonResponse({"success": False, "errors": form.errors}, status=400)
        messages.error(request, "No se pudo agregar el objeto. Revisa los datos ingresados.")
        return redirect("juego:inventario-ver", personaje_id=personaje.id)

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

    if is_ajax:
        return JsonResponse({"success": True, "cantidad": inv_item.cantidad})

    messages.success(
        request,
        f"Se agregó {cantidad} x {objeto.nombre} al inventario."
    )
    return redirect("juego:inventario-ver", personaje_id=personaje.id)


@login_required
@require_http_methods(["POST"])
def usar_consumible(request, personaje_id):
    personaje = get_object_or_404(Personaje, id=personaje_id, usuario=request.user)
    form = UseConsumableForm(request.POST, personaje=personaje)
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"

    if not form.is_valid():
        if is_ajax:
            return JsonResponse({"success": False, "errors": form.errors}, status=400)
        messages.error(request, "No se pudo usar el consumible. Revisa los datos ingresados.")
        return redirect("juego:inventario-ver", personaje_id=personaje.id)

    inv_item = Inventario.objects.select_related("objeto").get(
        id=form.cleaned_data["inventario_item_id"]
    )
    nombre_objeto = inv_item.objeto.nombre
    curacion_vida = inv_item.objeto.curacion_vida

    vida_antes = personaje.vida_actual
    if curacion_vida > 0:
        personaje.recuperar_vida(curacion_vida)
    personaje.refresh_from_db()
    vida_recuperada = max(0, personaje.vida_actual - vida_antes)

    if inv_item.cantidad <= 1:
        inv_item.delete()
    else:
        Inventario.objects.filter(id=inv_item.id).update(cantidad=F("cantidad") - 1)

    if is_ajax:
        return JsonResponse({"success": True})

    if vida_recuperada > 0:
        messages.success(request, f"Has usado 1 x {nombre_objeto} y recuperaste {vida_recuperada} de vida.")
    else:
        messages.success(request, f"Has usado 1 x {nombre_objeto}.")
    return redirect("juego:inventario-ver", personaje_id=personaje.id)


@login_required
@require_http_methods(["POST"])
def toggle_equipamiento_inventario(request, personaje_id):
    personaje = get_object_or_404(Personaje, id=personaje_id, usuario=request.user)
    inventario_item_id = request.POST.get("inventario_item_id")
    accion = request.POST.get("accion")

    inv_item = get_object_or_404(
        Inventario.objects.select_related("objeto"),
        id=inventario_item_id,
        personaje=personaje,
    )

    if inv_item.objeto.tipo != "equipable":
        messages.error(request, "Solo los objetos equipables se pueden equipar o desequipar.")
        return redirect("juego:inventario-ver", personaje_id=personaje.id)

    if accion == "equipar":
        Inventario.objects.filter(
            personaje=personaje,
            equipado=True,
            posicion_slot=inv_item.objeto.slot,
        ).exclude(id=inv_item.id).update(equipado=False, posicion_slot=None)

        inv_item.equipado = True
        inv_item.posicion_slot = inv_item.objeto.slot
        inv_item.save()
        messages.success(request, f"{inv_item.objeto.nombre} se ha equipado.")
    elif accion == "desequipar":
        inv_item.desequipar()
        messages.success(request, f"{inv_item.objeto.nombre} se ha desequipado.")
    else:
        messages.error(request, "Acción no válida.")

    return redirect("juego:inventario-ver", personaje_id=personaje.id)

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
            return render(request, 'registro.html', {'error': error})
        
        user = User.objects.create_user(username=username, password=password)
        login(request, user)
        return redirect('juego:personaje-lista')
    
    return render(request, 'registro.html')

def logout_view(request):
    logout(request)
    return redirect('juego:inicio-sesion')


class ZonaListView(ListView):
    model = Zona
    template_name = 'juego/zona_list.html'
    context_object_name = 'zonas'

    def get_queryset(self):
        return Zona.objects.annotate(
            num_enemigos=Count('enemigo'),
        ).order_by('nivel', 'nombre')


class ZonaDetailView(DetailView):
    model = Zona
    template_name = 'juego/zona_detail.html'
    context_object_name = 'zona'

    def get_queryset(self):
        return Zona.objects.select_related(
            'creada_por', 'actualizado_por'
        ).prefetch_related(
            'enemigos'
        )


class ZonaCreateView(AdminRequiredMixin, CreateView):
    model = Zona
    form_class = ZonaForm
    template_name = 'juego/zona_form.html'

    def get_success_url(self):
        return reverse('juego:zona-list')

    def form_valid(self, form):
        form.instance.creada_por = self.request.user
        form.instance.actualizado_por = self.request.user
        return super().form_valid(form)


class ZonaUpdateView(OwnerRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Zona
    form_class = ZonaForm
    template_name = 'juego/zona_form.html'

    def get_success_url(self):
        return reverse('juego:zona-list')

    def form_valid(self, form):
        form.instance.actualizado_por = self.request.user
        return super().form_valid(form)


class ZonaDeleteView(OwnerRequiredMixin, AdminRequiredMixin, DeleteView):
    model = Zona
    template_name = 'juego/zona_confirm_delete.html'

    def get_success_url(self):
        return reverse('juego:zona-list')


class EnemigoListView(ListView):
    model = Enemigo
    template_name = 'juego/enemigo_list.html'
    context_object_name = 'enemigos'

    def get_queryset(self):
        return Enemigo.objects.select_related(
            'zona', 'creada_por'
        ).order_by('zona', 'tipo', 'nombre')


class EnemigoDetailView(DetailView):
    model = Enemigo
    template_name = 'juego/enemigo_detail.html'
    context_object_name = 'enemigo'

    def get_queryset(self):
        return Enemigo.objects.select_related(
            'zona', 'creada_por'
        )


class EnemigoCreateView(AdminRequiredMixin, CreateView):
    model = Enemigo
    form_class = EnemigoForm
    template_name = 'juego/enemigo_form.html'

    def get_success_url(self):
        return reverse('juego:enemigo-list')

    def form_valid(self, form):
        form.instance.creada_por = self.request.user
        return super().form_valid(form)


class EnemigoUpdateView(OwnerRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Enemigo
    form_class = EnemigoForm
    template_name = 'juego/enemigo_form.html'

    def get_success_url(self):
        return reverse('juego:enemigo-list')


class EnemigoDeleteView(OwnerRequiredMixin, AdminRequiredMixin, DeleteView):
    model = Enemigo
    template_name = 'juego/enemigo_confirm_delete.html'

    def get_success_url(self):
        return reverse('juego:enemigo-list')


@login_required
def estadisticas_view(request):
    es_admin = request.user.groups.filter(
        name__in=['GAME_MASTER', 'ADMIN_CONTENIDO', 'ADMIN']
    ).exists() or request.user.is_staff or request.user.is_superuser

    personajes_qs = Personaje.objects.all() if es_admin else Personaje.objects.filter(usuario=request.user)
    combates_qs = Combate.objects.all() if es_admin else Combate.objects.filter(personaje__usuario=request.user)

    total_zonas = Zona.objects.count()
    total_enemigos = Enemigo.objects.count()
    total_jefes = Enemigo.objects.filter(tipo='jefe').count()

    stats = Enemigo.objects.aggregate(
        promedio_exp=Avg('exp_otorgada'),
        promedio_vida=Avg('vida_maxima')
    )
    
    # Stats reales basadas en Combate
    stats_combates = combates_qs.aggregate(
        total=Count('id'),
        promedio_exp_ganada=Avg('exp_ganada'),
    )
    
    # Mejores personajes (Win Rate)
    personajes_stats = personajes_qs.annotate(
        total_combates=Count('combate'),
        victorias=Count('combate', filter=Q(combate__resultado='victoria')),
    ).order_by('-victorias', '-nivel', 'nombre')

    context = {
        'total_zonas': total_zonas,
        'total_enemigos': total_enemigos,
        'total_jefes': total_jefes,
        'promedio_exp': stats['promedio_exp'] or 0,
        'promedio_vida': stats['promedio_vida'] or 0,
        'total_combates': stats_combates['total'] or 0,
        'promedio_exp_ganada': stats_combates['promedio_exp_ganada'] or 0,
        'personajes_stats': personajes_stats,
        'es_admin': es_admin,
    }

    return render(request, 'juego/estadisticas.html', context)


def incrementar_nivel_zona(zona_id):
    Zona.objects.filter(pk=zona_id).update(
        nivel=F('nivel') + 1
    )


def cambiar_tema_view(request):
    tema = request.GET.get('tema', 'claro')
    if tema not in ['claro', 'oscuro']:
        tema = 'claro'
    response = redirect(request.META.get('HTTP_REFERER') or reverse('juego:zona-list'))
    response.set_cookie('theme', tema, max_age=30 * 24 * 60 * 60)
    response.delete_cookie('tema_preferido')
    return response


def guardar_zona_sesion_view(request, pk):
    request.session['ultima_zona_id'] = pk
    request.session.set_expiry(24 * 60 * 60)
    return redirect('juego:zona-detail', pk=pk)

class CombateListView(LoginRequiredMixin, ListView):
    model = Combate
    template_name = 'juego/combate_list.html'
    context_object_name = 'combates'

    def test_func(self):
        personaje_id = self.kwargs.get('personaje_id')
        return Personaje.objects.filter(id=personaje_id, usuario=self.request.user).exists()

    def get_queryset(self):
        personaje_id = self.kwargs.get('personaje_id')
        return Combate.objects.filter(
            personaje_id=personaje_id,
            personaje__usuario=self.request.user
        ).select_related('enemigo', 'botin', 'zona')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        personaje_id = self.kwargs.get('personaje_id')
        context['personaje'] = get_object_or_404(Personaje, id=personaje_id, usuario=self.request.user)
        return context

import random as _random


def _calcular_danio(ataque, defensa):
    """Refined damage formula: (60-100% of atk) - (def//4), min 1."""
    base_dmg = _random.randint(int(ataque * 0.6), ataque)
    reduction = defensa // 4
    return max(1, base_dmg - reduction)


def _combate_state_key(personaje_id):
    return f'combate_turnos_{personaje_id}'


def _stats_efectivos(personaje):
    """Returns effective stats including bonuses from equipped inventory items."""
    ataque = personaje.ataque
    defensa = personaje.defensa
    velocidad = personaje.velocidad
    # Robust health handling
    base_vida = personaje.vida_actual if personaje.vida_actual is not None else personaje.salud_maxima
    vida = base_vida
    
    arma = None
    armadura = None
    for inv in personaje.inventario_items.filter(equipado=True).select_related('objeto'):
        obj = inv.objeto
        ataque += obj.bonus_ataque
        defensa += obj.bonus_defensa
        velocidad += obj.bonus_velocidad
        vida += obj.bonus_salud
        if obj.slot == 'arma':
            arma = obj.nombre
        elif obj.slot == 'armadura':
            armadura = obj.nombre
            
    return {
        'ataque': ataque, 
        'defensa': defensa, 
        'velocidad': velocidad,
        'vida_actual': vida, 
        'vida_max': personaje.salud_maxima + (vida - base_vida),
        'arma': arma, 
        'armadura': armadura
    }


class CombateCreateView(LoginRequiredMixin, View):
    """Prepara un combate por turnos seleccionando zona y enemigo."""

    def get(self, request, personaje_id):
        personaje = get_object_or_404(Personaje, id=personaje_id, usuario=request.user)
        
        # Vida actual para comprobación (si es None, usamos salud_maxima por seguridad)
        vida = personaje.vida_actual if personaje.vida_actual is not None else personaje.salud_maxima
        
        if vida <= 0:
            messages.error(request, f"¡{personaje.nombre} no tiene vida suficiente para combatir!")
            return redirect('juego:personaje-detalle', pk=personaje.id)
            
        form = CombateForm()
        return render(request, 'juego/combate_form.html', {
            'form': form, 'personaje': personaje,
        })

    def post(self, request, personaje_id):
        personaje = get_object_or_404(Personaje, id=personaje_id, usuario=request.user)

        vida = personaje.vida_actual if personaje.vida_actual is not None else personaje.salud_maxima
        
        if vida <= 0:
            messages.error(request, "Tu personaje no puede luchar sin vida.")
            return redirect('juego:personaje-detalle', pk=personaje.id)

        form = CombateForm(request.POST)
        if form.is_valid():
            enemigo = form.cleaned_data['enemigo']
            stats = _stats_efectivos(personaje)
            personaje_inicia = stats['velocidad'] >= enemigo.velocidad
            if stats['velocidad'] == enemigo.velocidad:
                personaje_inicia = _random.choice([True, False])

            state = {
                'personaje_id': personaje.id,
                'enemigo_id': enemigo.id,
                'personaje_nombre': personaje.nombre,
                'enemigo_nombre': enemigo.nombre,
                'zona_nombre': enemigo.zona.nombre,
                'es_jefe': enemigo.tipo == 'jefe',
                'personaje_vida': stats['vida_actual'],
                'personaje_vida_max': stats['vida_max'],
                'personaje_ataque': stats['ataque'],
                'personaje_defensa': stats['defensa'],
                'enemigo_vida': enemigo.vida_maxima,
                'enemigo_vida_max': enemigo.vida_maxima,
                'enemigo_ataque': enemigo.ataque,
                'enemigo_defensa': enemigo.defensa,
                'enemigo_exp': enemigo.exp_otorgada,
                'turno': 'personaje' if personaje_inicia else 'enemigo',
                'log': [
                    f"Comienza el combate contra {enemigo.nombre}.",
                    f"Turno inicial: {'Personaje' if personaje_inicia else 'Enemigo'}."
                ],
            }

            request.session[_combate_state_key(personaje.id)] = state
            request.session.modified = True
            return redirect('juego:combate-arena', personaje_id=personaje.id)

        return render(request, 'juego/combate_form.html', {
            'form': form, 'personaje': personaje,
        })


class CombateArenaView(LoginRequiredMixin, View):
    def _get_consumibles_curacion(self, personaje):
        return personaje.inventario_items.filter(
            objeto__tipo='consumible',
            objeto__curacion_vida__gt=0,
            cantidad__gt=0,
        ).select_related('objeto').order_by('objeto__nombre')

    def _get_state(self, request, personaje):
        key = _combate_state_key(personaje.id)
        state = request.session.get(key)
        if not state:
            return None
        if state.get('personaje_id') != personaje.id:
            return None
        return state

    def _save_state(self, request, personaje, state):
        request.session[_combate_state_key(personaje.id)] = state
        request.session.modified = True

    def _clear_state(self, request, personaje):
        key = _combate_state_key(personaje.id)
        if key in request.session:
            del request.session[key]
            request.session.modified = True

    def _finalizar_combate(self, request, personaje, state, resultado, exp_ganada=0):
        enemigo = get_object_or_404(Enemigo, id=state['enemigo_id'])

        bonus_salud = max(0, state['personaje_vida_max'] - personaje.salud_maxima)
        vida_base_final = max(0, state['personaje_vida'] - bonus_salud)
        personaje.vida_actual = min(personaje.salud_maxima, vida_base_final)
        if exp_ganada > 0:
            personaje.exp_actual += exp_ganada
        personaje.save()

        combate = Combate.objects.create(
            personaje=personaje,
            enemigo=enemigo,
            zona=enemigo.zona,
            tipo=enemigo.tipo,
            resultado=resultado,
            exp_ganada=exp_ganada,
            botin=None,
        )

        self._clear_state(request, personaje)
        return combate

    def get(self, request, personaje_id):
        personaje = get_object_or_404(Personaje, id=personaje_id, usuario=request.user)
        state = self._get_state(request, personaje)
        if not state:
            messages.info(request, 'Primero debes iniciar un combate.')
            return redirect('juego:combate-create', personaje_id=personaje.id)

        consumibles = self._get_consumibles_curacion(personaje)

        if state['turno'] == 'enemigo' and state['personaje_vida'] > 0 and state['enemigo_vida'] > 0:
            danio = _calcular_danio(state['enemigo_ataque'], state['personaje_defensa'])
            state['personaje_vida'] = max(0, state['personaje_vida'] - danio)
            state['log'].append(f"{state['enemigo_nombre']} ataca y hace {danio} de daño.")
            if state['personaje_vida'] <= 0:
                combate = self._finalizar_combate(request, personaje, state, 'derrota', 0)
                return render(request, 'juego/combate_arena.html', {
                    'personaje': personaje,
                    'estado': state,
                    'combate_finalizado': True,
                    'combate': combate,
                    'consumibles': consumibles,
                })
            state['turno'] = 'personaje'
            self._save_state(request, personaje, state)

        return render(request, 'juego/combate_arena.html', {
            'personaje': personaje,
            'estado': state,
            'combate_finalizado': False,
            'consumibles': consumibles,
        })

    def post(self, request, personaje_id):
        personaje = get_object_or_404(Personaje, id=personaje_id, usuario=request.user)
        state = self._get_state(request, personaje)
        if not state:
            messages.info(request, 'No hay combate activo. Inicia uno nuevo.')
            return redirect('juego:combate-create', personaje_id=personaje.id)

        accion = request.POST.get('accion')

        if state['turno'] != 'personaje':
            return redirect('juego:combate-arena', personaje_id=personaje.id)

        if accion == 'huir':
            if state['es_jefe']:
                state['log'].append('No puedes huir de un jefe.')
                self._save_state(request, personaje, state)
                return redirect('juego:combate-arena', personaje_id=personaje.id)

            combate = self._finalizar_combate(request, personaje, state, 'huida', 0)
            return render(request, 'juego/combate_arena.html', {
                'personaje': personaje,
                'estado': state,
                'combate_finalizado': True,
                'combate': combate,
            })

        if accion == 'usar_consumible':
            inventario_item_id = request.POST.get('inventario_item_id')
            if not inventario_item_id:
                state['log'].append('Debes seleccionar un consumible.')
                self._save_state(request, personaje, state)
                return redirect('juego:combate-arena', personaje_id=personaje.id)

            try:
                inv_item = Inventario.objects.select_related('objeto').get(
                    id=inventario_item_id,
                    personaje=personaje,
                    objeto__tipo='consumible',
                )
            except Inventario.DoesNotExist:
                state['log'].append('Consumible inválido para este personaje.')
                self._save_state(request, personaje, state)
                return redirect('juego:combate-arena', personaje_id=personaje.id)

            curacion = inv_item.objeto.curacion_vida or 0
            if curacion <= 0:
                state['log'].append('Ese consumible no cura vida.')
                self._save_state(request, personaje, state)
                return redirect('juego:combate-arena', personaje_id=personaje.id)

            if state['personaje_vida'] >= state['personaje_vida_max']:
                state['log'].append('Ya tienes la vida al máximo.')
                self._save_state(request, personaje, state)
                return redirect('juego:combate-arena', personaje_id=personaje.id)

            vida_antes = state['personaje_vida']
            state['personaje_vida'] = min(state['personaje_vida_max'], state['personaje_vida'] + curacion)
            vida_recuperada = state['personaje_vida'] - vida_antes

            if inv_item.cantidad <= 1:
                inv_item.delete()
            else:
                Inventario.objects.filter(id=inv_item.id).update(cantidad=F('cantidad') - 1)

            state['log'].append(
                f"{personaje.nombre} usa {inv_item.objeto.nombre} y recupera {vida_recuperada} de vida."
            )
            state['turno'] = 'enemigo'
            self._save_state(request, personaje, state)
            return redirect('juego:combate-arena', personaje_id=personaje.id)

        if accion != 'atacar':
            messages.error(request, 'Acción no válida.')
            return redirect('juego:combate-arena', personaje_id=personaje.id)

        danio = _calcular_danio(state['personaje_ataque'], state['enemigo_defensa'])
        state['enemigo_vida'] = max(0, state['enemigo_vida'] - danio)
        state['log'].append(f"{personaje.nombre} ataca y hace {danio} de daño.")

        if state['enemigo_vida'] <= 0:
            combate = self._finalizar_combate(request, personaje, state, 'victoria', state['enemigo_exp'])
            return render(request, 'juego/combate_arena.html', {
                'personaje': personaje,
                'estado': state,
                'combate_finalizado': True,
                'combate': combate,
            })

        state['turno'] = 'enemigo'
        self._save_state(request, personaje, state)
        return redirect('juego:combate-arena', personaje_id=personaje.id)


