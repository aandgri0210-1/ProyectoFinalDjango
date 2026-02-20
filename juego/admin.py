from django import forms
from django.contrib import admin
from .models import Inventario, Objeto, Personaje


class InventarioAdminForm(forms.ModelForm):
    class Meta:
        model = Inventario
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        objeto = cleaned_data.get('objeto')
        equipado = cleaned_data.get('equipado')

        if equipado and objeto:
            self.instance.posicion_slot = objeto.slot
        else:
            self.instance.posicion_slot = None

        return cleaned_data


@admin.register(Personaje)
class PersonajeAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'usuario', 'nivel', 'estado', 'vida_actual', 'salud_maxima')
    list_filter = ('estado', 'nivel')
    search_fields = ('nombre', 'usuario__username')
    ordering = ('-fecha_creacion',)


@admin.register(Objeto)
class ObjetoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'rareza', 'valor_venta', 'slot')
    list_filter = ('tipo', 'rareza')
    search_fields = ('nombre',)
    ordering = ('rareza', 'nombre')


@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    form = InventarioAdminForm
    list_display = ('personaje', 'objeto', 'cantidad', 'equipado', 'posicion_slot')
    list_filter = ('equipado', 'posicion_slot')
    search_fields = ('personaje__nombre', 'objeto__nombre')
    autocomplete_fields = ('personaje', 'objeto')
    exclude = ('posicion_slot',)

    def save_model(self, request, obj, form, change):
        if obj.equipado:
            obj.posicion_slot = obj.objeto.slot
        else:
            obj.posicion_slot = None
        super().save_model(request, obj, form, change)