from django.shortcuts import render
from django.views.generic import ListView,DetailView,CreateView,UpdateView,DeleteView
from django.urls import reverse_lazy
from .forms import ZonaForm, EnemigoForm
from .models import Zona, Enemigo
from .mixins import OwnerRequiredMixin

# Aquí irán tus vistas
# Vamos a crearlas paso a paso
class ZonaListView(ListView):
    model = Zona
    template_name = 'juego/zona_list.html'
    context_object_name = 'zonas'

class ZonaDetailView(DetailView):
    model = Zona
    template_name = 'juego/zona_detail.html'
    context_object_name = 'zona'

class ZonaCreateView(CreateView):
    model = Zona
    form_class = ZonaForm
    template_name = 'juego/zona_form.html'
    success_url = reverse_lazy('zona-list')


class ZonaUpdateView(OwnerRequiredMixin, UpdateView):
    model = Zona
    form_class = ZonaForm
    template_name = 'juego/zona_form.html'
    success_url = reverse_lazy('zona-list')

class ZonaDeleteView(OwnerRequiredMixin, DeleteView):
    model = Zona
    template_name = 'juego/zona_confirm_delete.html'
    success_url = reverse_lazy('zona-list')

class EnemigoListView(ListView):
    model = Enemigo
    template_name = 'juego/enemigo_list.html'
    context_object_name = 'enemigos'

class EnemigoDetailView(DetailView):
    model = Enemigo
    template_name = 'juego/enemigo_detail.html'
    context_object_name = 'enemigo'

class EnemigoCreateView(CreateView):
    model = Enemigo
    form_class = EnemigoForm
    template_name = 'juego/enemigo_form.html'

class EnemigoUpdateView(OwnerRequiredMixin, UpdateView):
    model = Enemigo
    form_class = EnemigoForm
    template_name = 'juego/enemigo_form.html'
    success_url = reverse_lazy('enemigo-list')

class EnemigoDeleteView(OwnerRequiredMixin, DeleteView):
    model = Enemigo
    template_name = 'juego/enemigo_confirm_delete.html'
    success_url = reverse_lazy('enemigo-list')