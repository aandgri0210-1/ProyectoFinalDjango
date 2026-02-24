from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

Usuario = get_user_model()


class Personaje(models.Model):

    ESTADO_CHOICES = (
        ('activo', 'Activo'),
        ('retirado', 'Retirado'),
    )

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='personajes'
    )

    nombre = models.CharField(
        max_length=20,
    )

    nivel = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )

    exp_actual = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )

    ataque = models.IntegerField(default=10)
    defensa = models.IntegerField(default=10)
    salud_maxima = models.IntegerField(default=50)
    vida_actual = models.IntegerField(default=50)
    velocidad = models.IntegerField(default=10)

    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='activo',
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Personaje'
        verbose_name_plural = 'Personajes'
        
        unique_together = (('usuario', 'nombre'),)
        
        constraints = [
            models.CheckConstraint(
                condition=models.Q(nivel__gte=1, nivel__lte=100),
                name='nivel_valido'
            ),
            models.CheckConstraint(
                condition=models.Q(exp_actual__gte=0),
                name='exp_no_negativa'
            ),
            models.CheckConstraint(
                condition=models.Q(vida_actual__gte=0),
                name='vida_actual_no_negativa'
            ),
            models.CheckConstraint(
                condition=models.Q(vida_actual__lte=models.F('salud_maxima')),
                name='vida_no_supera_maxima'
            ),
        ]
        
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.nombre} (Nivel {self.nivel})"

    def clean(self):
        super().clean()
        
        if self.vida_actual > self.salud_maxima:
            raise ValidationError("Vida actual no puede exceder salud máxima")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def recibir_danio(self, cantidad):
        self.vida_actual = max(0, self.vida_actual - cantidad)
        self.save()

    def recuperar_vida(self, cantidad):
        self.vida_actual = min(self.salud_maxima, self.vida_actual + cantidad)
        self.save()

    def ganar_exp(self, cantidad):
        self.exp_actual += cantidad
        self.save()

    def subir_nivel(self):
        if self.nivel < 100:
            self.nivel += 1
            self.exp_actual = 0
            self.save()

    def esta_vivo(self):
        return self.vida_actual > 0

class Objeto(models.Model):

    TIPO_CHOICES = (
        ('consumible', 'Consumible'),
        ('equipable', 'Equipable'),
    )

    RAREZA_CHOICES = (
        ('comun', 'Comun'),
        ('raro', 'Raro'),
        ('epico', 'Epico'),
        ('legendario', 'Legendario'),
    )

    SLOTS_CHOICES = (
        ('arma', 'Arma'),
        ('armadura', 'Armadura'),
        ('accesorio', 'Accesorio'),
    )

    nombre = models.CharField(
        max_length=50,
        unique=True,
    )

    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
    )

    rareza = models.CharField(
        max_length=20,
        choices=RAREZA_CHOICES,
    )

    efecto = models.TextField()

    valor_venta = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
    )

    slot = models.CharField(
        max_length=20,
        choices=SLOTS_CHOICES,
        blank=True,
        null=True,
    )

    bonus_ataque = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
    )

    bonus_defensa = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
    )

    bonus_salud = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
    )

    bonus_velocidad = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Objeto'
        verbose_name_plural = 'Objetos'

        constraints = [
            models.CheckConstraint(
                condition=models.Q(valor_venta__gte=0),
                name='valor_no_negativo'
            ),

            models.CheckConstraint(
                condition=models.Q(
                    models.Q(tipo='equipable', slot__isnull=False) |
                    models.Q(tipo='consumible', slot__isnull=True)
                ),
                name='consumible_no_tiene_slot'
            ),
        ]

        ordering = ['rareza', 'nombre']

    def __str__(self):
        return f"{self.nombre} [{self.get_rareza_display()}]"
    
    def clean(self):
        
        super().clean()
        
        if self.tipo == 'consumible' and self.slot:
            raise ValidationError({
                'slot': 'Los objetos de tipo consumible no pueden tener slot.'
            })
        
        if self.tipo == 'equipable' and not self.slot:
            raise ValidationError({
                'slot': 'Los objetos equipables deben tener un slot asignado'
            })
        
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        
    def es_equipable(self):
        return self.tipo == 'equipable'
    
class Inventario(models.Model):

    personaje = models.ForeignKey(
        Personaje,
        on_delete=models.CASCADE,
        related_name='inventario_items',
        related_query_name='inventario_item',
    )

    objeto = models.ForeignKey(
        Objeto,
        on_delete=models.CASCADE,
        related_name='en_inventarios',
        related_query_name='en_inventario',
    )

    cantidad = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
    )

    equipado = models.BooleanField(
        default=False,
    )

    posicion_slot = models.CharField(
        max_length=20,
        choices=Objeto.SLOTS_CHOICES,
        blank=True,
        null=True,
    )

    fecha_adquisicion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Inventario'
        verbose_name_plural = 'Inventario'

        unique_together = [['personaje', 'objeto']]

        constraints = [
            models.CheckConstraint(
                condition=models.Q(cantidad__gte=1),
                name='cantidad_minima_uno'
            ),

            models.CheckConstraint(
                condition=models.Q(
                    models.Q(equipado=False) |
                    models.Q(equipado=True, posicion_slot__isnull=False)
                ),
                name='equipado_requiere_slot'
            ),
        ]

        ordering = ['-equipado', '-fecha_adquisicion']

    def __str__(self):
        equipado_str = " [Equipado]" if self.equipado else ""
        return f"{self.objeto.nombre} x{self.cantidad}{equipado_str} - {self.personaje.nombre}"

    def clean(self):
        super().clean()
        if self.equipado and self.objeto.tipo != 'equipable':
            raise ValidationError('Solo los objetos equipables pueden estar equipados.')
        
        if self.equipado and self.posicion_slot != self.objeto.slot:
            raise ValidationError(f'El slot debe coincidir con el del objeto.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def equipar(self):
        if self.objeto.tipo != 'equipable':
            raise ValidationError('No puedes equipar un objeto consumible.')

        self.equipado = True
        self.posicion_slot = self.objeto.slot
        self.save()

    def desequipar(self):
        self.equipado = False
        self.posicion_slot = None
        self.save()

    def agregar_cantidad(self, cantidad):
        if cantidad < 1:
            raise ValidationError('La cantidad a agregar debe ser mayor a 0.')

        self.cantidad += cantidad
        self.save()

    def reducir_cantidad(self, cantidad):
        if cantidad < 1:
            raise ValidationError('La cantidad a reducir debe ser mayor a 0.')

        if cantidad >= self.cantidad:
            self.delete()
        else:
            self.cantidad -= cantidad
            self.save()

    def usar_consumible(self):
        if self.objeto.tipo != 'consumible':
            raise ValidationError('Solo puedes usar objetos consumibles.')

        if self.equipado:
            raise ValidationError('No puedes usar un objeto que está equipado.')

        self.reducir_cantidad(1)