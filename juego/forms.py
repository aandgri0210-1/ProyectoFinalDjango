from django import forms
from django.core.exceptions import ValidationError

from .models import Inventario, Objeto, Personaje


class PersonajeForm(forms.ModelForm):
    class Meta:
        model = Personaje
        fields = [
            'nombre',
            'nivel',
            'exp_actual',
            'ataque',
            'defensa',
            'salud_maxima',
            'vida_actual',
            'velocidad',
            'estado',
        ]

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.usuario = usuario

        if usuario and not usuario.groups.filter(
            name__in=['GAME_MASTER', 'ADMIN_CONTENIDO', 'ADMIN']
        ).exists():
            self.fields.pop('estado', None)

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if not nombre:
            raise ValidationError('El nombre del personaje es obligatorio.')
        if len(nombre) < 3:
            raise ValidationError('El nombre debe tener al menos 3 caracteres.')

        if not self.usuario:
            return nombre

        queryset = Personaje.objects.filter(usuario=self.usuario, nombre=nombre)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise ValidationError(f'Ya existe un personaje con el nombre "{nombre}".')
        return nombre

    def clean(self):
        cleaned_data = super().clean()

        nivel = cleaned_data.get('nivel')
        exp_actual = cleaned_data.get('exp_actual')
        ataque = cleaned_data.get('ataque')
        defensa = cleaned_data.get('defensa')
        salud_maxima = cleaned_data.get('salud_maxima')
        vida_actual = cleaned_data.get('vida_actual')
        velocidad = cleaned_data.get('velocidad')

        if nivel is not None and (nivel < 1 or nivel > 100):
            raise ValidationError('El nivel debe estar entre 1 y 100.')
        if exp_actual is not None and exp_actual < 0:
            raise ValidationError('La EXP actual no puede ser negativa.')

        if ataque is not None and (ataque < 5 or ataque > 100):
            raise ValidationError('El ataque debe estar entre 5 y 100.')
        if defensa is not None and (defensa < 5 or defensa > 100):
            raise ValidationError('La defensa debe estar entre 5 y 100.')
        if salud_maxima is not None and (salud_maxima < 10 or salud_maxima > 500):
            raise ValidationError('La salud maxima debe estar entre 10 y 500.')
        if velocidad is not None and (velocidad < 1 or velocidad > 100):
            raise ValidationError('La velocidad debe estar entre 1 y 100.')

        if vida_actual is not None and salud_maxima is not None:
            if vida_actual < 0:
                raise ValidationError('La vida actual no puede ser negativa.')
            if vida_actual > salud_maxima:
                raise ValidationError('La vida actual no puede exceder la salud maxima.')

        if nivel is not None and exp_actual is not None:
            exp_minima = (nivel - 1) * 100
            if exp_actual < exp_minima:
                raise ValidationError(
                    'La EXP actual no es coherente con el nivel indicado.'
                )

        return cleaned_data


class AddInventoryItemForm(forms.Form):
    objeto = forms.ModelChoiceField(
        queryset=Objeto.objects.all(),
        label='Selecciona un objeto',
    )
    cantidad = forms.IntegerField(
        min_value=1,
        initial=1,
    )

    def clean_cantidad(self):
        cantidad = self.cleaned_data.get('cantidad')
        if cantidad is None or cantidad < 1:
            raise ValidationError('La cantidad debe ser al menos 1.')
        return cantidad


class UseConsumableForm(forms.Form):
    inventario_item_id = forms.IntegerField(widget=forms.HiddenInput())

    def __init__(self, *args, personaje=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.personaje = personaje

    def clean_inventario_item_id(self):
        inventario_item_id = self.cleaned_data.get('inventario_item_id')
        if not inventario_item_id:
            raise ValidationError('El objeto no es valido.')

        try:
            inv_item = Inventario.objects.select_related('objeto').get(
                id=inventario_item_id
            )
        except Inventario.DoesNotExist:
            raise ValidationError('El objeto no existe en el inventario.')

        if self.personaje and inv_item.personaje_id != self.personaje.id:
            raise ValidationError('Este objeto no pertenece a tu personaje.')
        if inv_item.objeto.tipo != 'consumible':
            raise ValidationError('Solo puedes usar objetos consumibles.')
        if inv_item.cantidad < 1:
            raise ValidationError('No tienes unidades disponibles de este objeto.')

        return inventario_item_id