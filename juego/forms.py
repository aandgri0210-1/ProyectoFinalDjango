from django import forms
from django.core.exceptions import ValidationError
from .models import Zona, Enemigo


class ZonaForm(forms.ModelForm):
    class Meta:
        model = Zona
        fields = ['nombre', 'nivel', 'descripcion', 'dificultad', 'activa']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'nivel': forms.NumberInput(attrs={'min': 1, 'max': 100}),

        }

    def clean_nombre(self):
        """Valida que el nombre tenga mínimo 2 caracteres"""
        nombre = self.cleaned_data.get('nombre')
        if not nombre or len(nombre.strip()) < 3:
            raise ValidationError("El nombre debe tener mínimo 3 caracteres")

        existing = Zona.objects.filter(nombre__iexact=nombre)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)

        if existing.exists():
            raise ValidationError("Ya existe zona con este nombre")

        return nombre.strip()

    def clean_nivel(self):
        nivel = self.cleaned_data.get('nivel')

        if nivel and (nivel < 1 or nivel > 100):
            raise ValidationError("El nivel debe estar entre 1 y 100")
        return nivel

    def clean(self):
        cleaned_data = super().clean()
        dificultad = cleaned_data.get('dificultad')
        nivel = cleaned_data.get('nivel')

        if dificultad == 'pro' and nivel and nivel < 30:
            raise ValidationError("La zona de dificultad Pro debe de tener minimo nivel 30")
        return cleaned_data


class EnemigoForm(forms.ModelForm):
    class Meta:
        model = Enemigo
        fields = ['nombre', 'tipo', 'rareza', 'zona', 'descripcion',
                  'vida_maxima', 'ataque', 'defensa', 'velocidad',
                  'exp_otorgada', 'oro_otorgado', 'activo']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'vida_maxima': forms.NumberInput(attrs={'min': 1}),
            'ataque': forms.NumberInput(attrs={'min': 1}),
            'defensa': forms.NumberInput(attrs={'min': 0}),
            'velocidad': forms.NumberInput(attrs={'min': 1}),
            'exp_otorgada': forms.NumberInput(attrs={'min': 0}),
            'oro_otorgado': forms.NumberInput(attrs={'min': 0}),
        }

    def clean_nombre(self):

        nombre = self.cleaned_data.get('nombre')

        if not nombre or len(nombre.strip()) < 2:
            raise ValidationError("El nombre debe tener mínimo 2 caracteres")

        return nombre.strip()

    def clean(self):
        cleaned_data = super().clean()

        tipo = cleaned_data.get('tipo')
        zona = cleaned_data.get('zona')
        rareza = cleaned_data.get('rareza')
        vida_maxima = cleaned_data.get('vida_maxima')
        exp = cleaned_data.get('exp_otorgada')

        if tipo == 'jefe':

            if rareza not in ['epico', 'legendario']:
                raise ValidationError("Los Jefes deben ser Epicos o Legendarios")

            if vida_maxima and vida_maxima < 100:
                raise ValidationError("Los Jefes deben de tener minimo 100 de vida")

            if exp and exp < 100:
                raise ValidationError("Los Jefes deben de tener minimo 100 de exp")

            if zona:
                existing_jefes = Enemigo.objects.filter(tipo='jefe', zona=zona)

                if self.instance.pk:
                    existing_jefes = existing_jefes.exclude(pk=self.instance.pk)

                if existing_jefes.exists():
                    raise ValidationError(f"Ya existe el Jefe en la zona {zona.nombre}")

        return cleaned_data

