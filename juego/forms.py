from django import forms
from django.core.exceptions import ValidationError

from .models import Enemigo, Combate, Inventario, Objeto, Personaje, Zona


class PersonajeForm(forms.ModelForm):
    class Meta:
        model = Personaje
        fields = [
            'nombre',
            'exp_actual',
            'ataque',
            'defensa',
            'salud_maxima',
            'vida_actual',
            'velocidad',
            'estado',
        ]

    def __init__(self, *args, usuario=None, es_editable=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.usuario = usuario
        self.es_editable = es_editable
        
        # Si es un personaje nuevo (no tiene pk), solo mostrar nombre
        if not self.instance.pk:
            # Crear personaje: solo nombre
            fields_to_keep = ['nombre']
            if usuario and usuario.groups.filter(
                name__in=['GAME_MASTER', 'ADMIN_CONTENIDO', 'ADMIN']
            ).exists():
                fields_to_keep.append('estado')
            
            # Remover todos los campos excepto nombre (y estado si es admin)
            fields_to_remove = [f for f in self.fields.keys() if f not in fields_to_keep]
            for field in fields_to_remove:
                self.fields.pop(field, None)
        else:
            # Editar personaje: mostrar todos
            if usuario and not usuario.groups.filter(
                name__in=['GAME_MASTER', 'ADMIN_CONTENIDO', 'ADMIN']
            ).exists():
                self.fields.pop('estado', None)
                
            # Si no es editable, hacer todos los campos disabled
            if not es_editable:
                for field in self.fields.values():
                    field.disabled = True

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
        
        # Validación: Si es una creación nueva, verificar que no exista ya un personaje activo
        if not self.instance.pk and self.usuario:
            if Personaje.objects.filter(usuario=self.usuario, estado='activo').exists():
                raise ValidationError(
                    'Ya tienes un personaje activo. Un usuario solo puede tener un personaje activo.'
                )

        exp_actual = cleaned_data.get('exp_actual')
        ataque = cleaned_data.get('ataque')
        defensa = cleaned_data.get('defensa')
        salud_maxima = cleaned_data.get('salud_maxima')
        vida_actual = cleaned_data.get('vida_actual')
        velocidad = cleaned_data.get('velocidad')

        if exp_actual is not None and exp_actual < 0:
            raise ValidationError('La EXP actual no puede ser negativa.')
        if exp_actual is not None and exp_actual > 9999:
            raise ValidationError('La máxima experiencia es 9999 (Nivel 100).')

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


class ZonaForm(forms.ModelForm):
    class Meta:
        model = Zona
        fields = ['nombre', 'nivel', 'descripcion', 'dificultad', 'activa']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'nivel': forms.NumberInput(attrs={'min': 1, 'max': 100, 'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'dificultad': forms.Select(attrs={'class': 'form-control'}),
            'activa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if not nombre or len(nombre.strip()) < 3:
            raise ValidationError('El nombre debe tener minimo 3 caracteres')

        existing = Zona.objects.filter(nombre__iexact=nombre)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)

        if existing.exists():
            raise ValidationError('Ya existe una zona con este nombre')

        return nombre.strip()

    def clean_nivel(self):
        nivel = self.cleaned_data.get('nivel')
        if nivel and (nivel < 1 or nivel > 100):
            raise ValidationError('El nivel debe estar entre 1 y 100')
        return nivel

    def clean(self):
        cleaned_data = super().clean()
        dificultad = cleaned_data.get('dificultad')
        nivel = cleaned_data.get('nivel')

        if dificultad == 'pro' and nivel and nivel < 30:
            raise ValidationError('La zona de dificultad Pro debe tener minimo nivel 30')

        return cleaned_data


class EnemigoForm(forms.ModelForm):
    class Meta:
        model = Enemigo
        fields = [
            'nombre',
            'tipo',
            'rareza',
            'zona',
            'descripcion',
            'vida_maxima',
            'ataque',
            'defensa',
            'velocidad',
            'exp_otorgada',
            'oro_otorgado',
            'activo',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'rareza': forms.Select(attrs={'class': 'form-control'}),
            'zona': forms.Select(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'vida_maxima': forms.NumberInput(attrs={'min': 1, 'class': 'form-control'}),
            'ataque': forms.NumberInput(attrs={'min': 1, 'class': 'form-control'}),
            'defensa': forms.NumberInput(attrs={'min': 0, 'class': 'form-control'}),
            'velocidad': forms.NumberInput(attrs={'min': 1, 'class': 'form-control'}),
            'exp_otorgada': forms.NumberInput(attrs={'min': 0, 'class': 'form-control'}),
            'oro_otorgado': forms.NumberInput(attrs={'min': 0, 'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')

        if not nombre or len(nombre.strip()) < 2:
            raise ValidationError('El nombre debe tener minimo 2 caracteres')

        return nombre.strip()

    def clean_vida_maxima(self):
        vida = self.cleaned_data.get('vida_maxima')
        if vida and vida < 1:
            raise ValidationError('La vida maxima debe ser al menos 1')
        return vida

    def clean_exp_otorgada(self):
        exp = self.cleaned_data.get('exp_otorgada')
        if exp is not None and exp < 0:
            raise ValidationError('La EXP otorgada no puede ser negativa')
        return exp

    def clean(self):
        cleaned_data = super().clean()

        tipo = cleaned_data.get('tipo')
        zona = cleaned_data.get('zona')
        rareza = cleaned_data.get('rareza')
        vida_maxima = cleaned_data.get('vida_maxima')
        exp = cleaned_data.get('exp_otorgada')

        if tipo == 'jefe':
            if rareza not in ['epico', 'legendario']:
                raise ValidationError('Los Jefes deben ser de rareza Epica o Legendaria')

            if vida_maxima and vida_maxima < 100:
                raise ValidationError('Los Jefes deben tener minimo 100 de vida')

            if exp and exp < 100:
                raise ValidationError('Los Jefes deben otorgar minimo 100 de EXP')

            if zona:
                existing_jefes = Enemigo.objects.filter(tipo='jefe', zona=zona)

                if self.instance.pk:
                    existing_jefes = existing_jefes.exclude(pk=self.instance.pk)

                if existing_jefes.exists():
                    raise ValidationError(
                        f"Ya existe un Jefe en la zona '{zona.nombre}'. Solo puede haber un jefe por zona."
                    )

        return cleaned_data

class EnemigoSelectWidget(forms.Select):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        # En Django >= 1.11, value puede ser un objeto o el ID
        val = value.value if hasattr(value, 'value') else value
        if val:
            try:
                obj = self.choices.queryset.get(pk=val)
                option['attrs']['data-zona-id'] = obj.zona_id
            except (Enemigo.DoesNotExist, ValueError, AttributeError):
                pass
        return option

class CombateForm(forms.ModelForm):
    enemigo = forms.ModelChoiceField(queryset=Enemigo.objects.all(), widget=EnemigoSelectWidget(attrs={'class': 'form-control'}))

    class Meta:
        model = Combate
        fields = ['zona', 'enemigo']
        widgets = {
            'enemigo': forms.Select(attrs={'class': 'form-control'}),
            'zona': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['zona'].queryset = Zona.objects.filter(activa=True).order_by('nivel', 'nombre')
        self.fields['zona'].empty_label = '— Selecciona una zona —'
        self.fields['enemigo'].queryset = Enemigo.objects.filter(activo=True).select_related('zona').order_by('zona__nivel', 'zona__nombre', 'nombre')

    def clean(self):
        cleaned_data = super().clean()
        zona = cleaned_data.get('zona')
        enemigo = cleaned_data.get('enemigo')

        if zona and enemigo and enemigo.zona_id != zona.id:
            raise ValidationError('El enemigo seleccionado no pertenece a la zona elegida.')
            
        return cleaned_data


class IniciarCombateForm(forms.Form):
    TIPO_CHOICES = [
        ('normal', 'Enemigo Normal'),
        ('jefe', 'Jefe de Zona'),
    ]
    zona = forms.ModelChoiceField(
        queryset=Zona.objects.filter(activa=True).order_by('nivel', 'nombre'),
        label='Zona de combate',
        empty_label='— Selecciona una zona —',
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_zona'}),
    )
    tipo = forms.ChoiceField(
        choices=Combate.TIPO_CHOICES,
        label='Tipo de enemigo',
        widget=forms.RadioSelect(attrs={'class': 'tipo-radio'}),
        initial='normal',
    )

    def clean(self):
        cleaned_data = super().clean()
        zona = cleaned_data.get('zona')
        tipo = cleaned_data.get('tipo')
        if zona and tipo:
            disponibles = Enemigo.objects.filter(zona=zona, tipo=tipo, activo=True)
            if not disponibles.exists():
                raise forms.ValidationError(
                    f'No hay enemigos de tipo "{tipo}" activos en la zona "{zona.nombre}".'
                )
        return cleaned_data


class SeleccionarEnemigoForm(forms.Form):
    enemigo = forms.ModelChoiceField(
        queryset=Enemigo.objects.none(),
        label='Elige tu adversario',
        empty_label=None,
        widget=forms.RadioSelect(attrs={'class': 'enemigo-radio'}),
    )

    def __init__(self, *args, zona=None, tipo=None, **kwargs):
        super().__init__(*args, **kwargs)
        if zona and tipo:
            self.fields['enemigo'].queryset = Enemigo.objects.filter(
                zona=zona, tipo=tipo, activo=True
            ).order_by('nombre')