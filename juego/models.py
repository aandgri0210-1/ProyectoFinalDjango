from django.db import models
from django.contrib.auth.models import User

# Aquí irán tus modelos de contenido del juego
# Vamos a crearlos paso a paso
class Zona(models.Model):
    nombre = models.CharField(max_length=100)
    nivel = models.PositiveIntegerField(default=1)
    descripcion = models.TextField(blank=True, null=True)
    dificultad = models.CharField(max_length=20,choices=[
        ('normal','Normal'),
        ('avanzado','Avanzado'),
        ('dificil','Dificil'),
        ('pro','Pro')
    ])
    activa = models.BooleanField(default=True)
    creada_por = models.ForeignKey(User, on_delete=models.PROTECT, related_name='zonas_creadas')
    actualizado_por = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='zonas_actualizadas')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'zona'
        ordering = ['nivel', 'nombre']
        verbose_name = 'Zona'
        verbose_name_plural = 'Zonas'

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')

        if not nombre or len(nombre.strip) < 3:
            raise ValidationError("El nombre debe tener minimo 3 caracteres")

        existing = Zona.objects.filter(nombre__iexact=nombre)
        if self.instance.pk:
            existing = existing.exclude(pk.self.instance.pk)


    def __str__(self):
        return self.nombre




class Enemigo(models.Model):
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20,choices=[
        ('normal','Normal'),
        ('jefe', 'Jefe')
    ])
    zona = models.ForeignKey(Zona, on_delete=models.CASCADE, related_name='enemigos')
    rareza = models.CharField(max_length=20,choices=[
        ('comun','Comun'),
        ('raro','Raro'),
        ('epico','Epico'),
        ('legendario','Legenario')
    ])
    activo = models.BooleanField(default=True)
    creada_por = models.ForeignKey(User, on_delete=models.PROTECT, related_name='enemigos_creados')
    descripcion = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    vida_maxima = models.PositiveIntegerField(default=10)
    ataque = models.PositiveIntegerField(default=5)
    defensa = models.PositiveIntegerField(default=2)
    velocidad = models.PositiveIntegerField(default=3)

    exp_otorgada = models.PositiveIntegerField(default=10)
    oro_otorgado = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['zona', 'tipo', 'nombre']
        verbose_name = 'Enemigo'
        verbose_name_plural = 'Enemigos'

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()}) - {self.zona.nombre}"

