from django import forms
from django.core.exceptions import ValidationError

from .models import Inventario, Objeto, Personaje


class PersonajesForm(forms.ModelForm):
    class Meta:
        model = Personaje
        fields = ['nombre', 'ataque', 'defensa', 'salud_maxima', 'vida_actual', 'velocidad']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del personaje:',
                'maxlength': '20',
            }),
            'ataque': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '100',
                'placeholder': 'Ataque base (1-100)',
            }),
            'defensa': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '100',
                'placeholder': 'Defensa base (1-100)',
            }),
            'salud_maxima': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '10',
                'max': '500',
                'placeholder': 'Salud máxima (10-500)',
            }),
            'vida_actual': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': 'Vida actual',
            }),
            'velocidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '100',
                'placeholder': 'Velocidad (1-100)',
            }),
        }
        error_messages = {
            'nombre': {
                'required': 'El nombre del personaje es obligatorio.',
                'max_length': 'El nombre no puede exceder 20 caracteres.',
            },
        }

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.usuario = usuario
        self.fields['nombre'].required = True

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if not nombre:
            raise ValidationError('El nombre del personaje no puede estar vacío.')
        if len(nombre) < 3:
            raise ValidationError('El nombre debe tener al menos 3 caracteres.')
        queryset = Personaje.objects.filter(usuario=self.usuario, nombre=nombre)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise ValidationError(f'Ya existe un personaje con el nombre "{nombre}".')
        return nombre

    def clean_salud_maxima(self):
        salud_maxima = self.cleaned_data.get('salud_maxima')
        if salud_maxima and salud_maxima < 10:
            raise ValidationError('La salud máxima debe ser mayor a 10.')
        if salud_maxima and salud_maxima > 500:
            raise ValidationError('La salud máxima no puede exceder 500.')
        return salud_maxima

    def clean(self):
        cleaned_data = super().clean()
        vida_actual = cleaned_data.get('vida_actual')
        salud_maxima = cleaned_data.get('salud_maxima')
        if vida_actual is not None and salud_maxima is not None:
            if vida_actual > salud_maxima:
                raise ValidationError(
                    'La vida actual no puede exceder la salud máxima.'
                )
            if vida_actual < 0:
                raise ValidationError('La vida actual no puede ser negativa.')
        return cleaned_data


class ObjetoForm(forms.ModelForm):
    class Meta:
        model = Objeto
        fields = [
            'nombre',
            'tipo',
            'rareza',
            'efecto',
            'valor_venta',
            'slot',
            'bonus_ataque',
            'bonus_defensa',
            'bonus_salud',
            'bonus_velocidad',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del objeto',
                'maxlength': '50',
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-control',
            }),
            'rareza': forms.Select(attrs={
                'class': 'form-control',
            }),
            'slot': forms.Select(attrs={
                'class': 'form-control',
                'required': False,
            }),
            'efecto': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción del efecto (ej: +10 EXP cuando se usa)',
            }),
            'valor_venta': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': 'Valor en monedas del juego',
            }),
            'bonus_ataque': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'value': '0',
                'placeholder': 'Bonus de ataque (0 si no aplica)',
            }),
            'bonus_defensa': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'value': '0',
                'placeholder': 'Bonus de defensa (0 si no aplica)',
            }),
            'bonus_salud': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'value': '0',
                'placeholder': 'Bonus de salud (0 si no aplica)',
            }),
            'bonus_velocidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'value': '0',
                'placeholder': 'Bonus de velocidad (0 si no aplica)',
            }),
        }

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        queryset = Objeto.objects.filter(nombre=nombre)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise ValidationError(f'Ya existe un objeto con el nombre "{nombre}".')
        return nombre

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        slot = cleaned_data.get('slot')
        bonus_ataque = cleaned_data.get('bonus_ataque') or 0
        bonus_defensa = cleaned_data.get('bonus_defensa') or 0
        bonus_salud = cleaned_data.get('bonus_salud') or 0
        bonus_velocidad = cleaned_data.get('bonus_velocidad') or 0

        if tipo == 'consumible' and slot:
            raise ValidationError({
                'slot': 'Los objetos consumibles no pueden tener un slot asignado.'
            })
        if tipo == 'equipable' and not slot:
            raise ValidationError({
                'slot': 'Los objetos equipables deben tener un slot asignado.'
            })
        if tipo == 'consumible':
            tiene_bonos = any([
                bonus_ataque,
                bonus_defensa,
                bonus_salud,
                bonus_velocidad,
            ])
            if tiene_bonos:
                raise ValidationError(
                    'Los objetos consumibles no pueden tener bonificaciones. '
                    'Los bonos son solo para equipables'
                )
        return cleaned_data


class InventarioForm(forms.Form):
    inventario_item = forms.ModelChoiceField(
        queryset=Inventario.objects.none(),
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        label='Selecciona un objeto',
    )

    ACCIONES = [
        ('equipar', 'Equipar objeto'),
        ('desequipar', 'Desequipar objeto'),
        ('usar', 'Usar consumible'),
    ]

    accion = forms.ChoiceField(
        choices=ACCIONES,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input',
        }),
        label='¿Qué quieres hacer?',
    )

    def __init__(self, *args, personaje=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.personaje = personaje
        if personaje:
            self.fields['inventario_item'].queryset = Inventario.objects.filter(
                personaje=personaje
            ).select_related('objeto')

    def clean(self):
        cleaned_data = super().clean()
        inventario_item = cleaned_data.get('inventario_item')
        accion = cleaned_data.get('accion')

        if not inventario_item or not accion:
            return cleaned_data

        objeto = inventario_item.objeto

        if accion == 'equipar':
            if objeto.tipo != 'equipable':
                raise ValidationError(
                    f'No puedes equipar "{objeto.nombre}" porque no es un objeto equipable.'
                )
            conflicto = Inventario.objects.filter(
                personaje=self.personaje,
                equipado=True,
                posicion_slot=objeto.slot
            ).exclude(pk=inventario_item.pk)
            if conflicto.exists():
                conflicto_obj = conflicto.first()
                raise ValidationError(
                    f'Ya tienes un objeto equipado en {objeto.get_slot_display()}. '
                    f'{conflicto_obj.objeto.nombre}.'
                )
        elif accion == 'desequipar':
            if not inventario_item.equipado:
                raise ValidationError(
                    f'"{objeto.nombre}" no esta equipado. No puedes desequipar.'
                )
        elif accion == 'usar':
            if objeto.tipo != 'consumible':
                raise ValidationError(
                    f'No puedes usar "{objeto.nombre}" porque no es un objeto consumible.'
                )
            if inventario_item.equipado:
                raise ValidationError(
                    f'No puedes usar "{objeto.nombre}" mientras este equipado. '
                    'Desequipalo primero.'
                )

        return cleaned_data