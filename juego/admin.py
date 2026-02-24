from django.contrib import admin
from .models import Inventario, Objeto, Personaje


@admin.register(Personaje)
class PersonajeAdmin(admin.ModelAdmin):
    pass


@admin.register(Objeto)
class ObjetoAdmin(admin.ModelAdmin):
    pass


@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    pass