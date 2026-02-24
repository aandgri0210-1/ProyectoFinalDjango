from django.contrib import admin
from .forms import EnemigoForm, ZonaForm
from .models import Enemigo, Inventario, Objeto, Personaje, Zona


@admin.register(Personaje)
class PersonajeAdmin(admin.ModelAdmin):
    pass


@admin.register(Objeto)
class ObjetoAdmin(admin.ModelAdmin):
    pass


@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    pass


@admin.register(Zona)
class ZonaAdmin(admin.ModelAdmin):
    form = ZonaForm
    list_display = ('nombre', 'nivel', 'dificultad', 'activa')
    list_filter = ('dificultad', 'activa')
    search_fields = ('nombre', 'descripcion')

    def save_model(self, request, obj, form, change):
        if not change:
            obj.creada_por = request.user
        obj.actualizado_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(Enemigo)
class EnemigoAdmin(admin.ModelAdmin):
    form = EnemigoForm
    list_display = ('nombre', 'tipo', 'rareza', 'zona', 'vida_maxima', 'activo')
    list_filter = ('tipo', 'rareza', 'zona', 'activo')
    search_fields = ('nombre', 'descripcion', 'zona__nombre')

    def save_model(self, request, obj, form, change):
        if not change:
            obj.creada_por = request.user
        super().save_model(request, obj, form, change)