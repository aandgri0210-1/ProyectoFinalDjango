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
        validators=[MinValueValidator(0), MaxValueValidator(9999)]
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
            models.UniqueConstraint(
                fields=['usuario'],
                name='usuario_un_personaje',
                condition=models.Q(estado='activo')
            ),
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

    @staticmethod
    def calcular_nivel_desde_exp(exp_actual):
        nivel = min((exp_actual // 100) + 1, 100)
        return nivel

    def obtener_exp_requerida_nivel_actual(self):
        if self.nivel >= 100:
            return (9900, 9999)
        exp_minima = (self.nivel - 1) * 100
        exp_maxima = (self.nivel * 100) - 1
        return (exp_minima, exp_maxima)

    def obtener_progreso_nivel(self):
        exp_minima, _ = self.obtener_exp_requerida_nivel_actual()
        return self.exp_actual - exp_minima

    def clean(self):
        super().clean()
        
        if self.vida_actual > self.salud_maxima:
            raise ValidationError("Vida actual no puede exceder salud máxima")
        
        self.nivel = self.calcular_nivel_desde_exp(self.exp_actual)

    def aplicar_bonus_subida_nivel(self, niveles_ganados):
        if niveles_ganados <= 0:
            return

        self.ataque += niveles_ganados
        self.defensa += niveles_ganados
        self.salud_maxima += niveles_ganados
        self.velocidad += niveles_ganados

    def save(self, *args, **kwargs):
        nivel_anterior = None
        if self.pk:
            nivel_anterior = Personaje.objects.filter(pk=self.pk).values_list("nivel", flat=True).first()

        nivel_nuevo = self.calcular_nivel_desde_exp(self.exp_actual)

        if nivel_anterior is None:
            nivel_anterior = nivel_nuevo

        niveles_ganados = max(0, nivel_nuevo - nivel_anterior)
        self.aplicar_bonus_subida_nivel(niveles_ganados)

        self.nivel = nivel_nuevo
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
            siguiente_nivel = self.nivel + 1
            self.exp_actual = (siguiente_nivel - 1) * 100
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

    curacion_vida = models.IntegerField(
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

        if self.tipo == 'consumible' and self.curacion_vida < 0:
            raise ValidationError({
                'curacion_vida': 'La curación de vida no puede ser negativa.'
            })
        
        if self.tipo == 'equipable' and not self.slot:
            raise ValidationError({
                'slot': 'Los objetos equipables deben tener un slot asignado'
            })

        if self.tipo == 'equipable' and self.curacion_vida > 0:
            raise ValidationError({
                'curacion_vida': 'Solo los objetos consumibles pueden curar vida.'
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


class Zona(models.Model):
    DIFICULTAD_CHOICES = (
        ('normal', 'Normal'),
        ('avanzado', 'Avanzado'),
        ('dificil', 'Dificil'),
        ('pro', 'Pro'),
    )

    nombre = models.CharField(max_length=100)
    nivel = models.PositiveIntegerField(default=1)
    descripcion = models.TextField(blank=True, null=True)
    dificultad = models.CharField(max_length=20, choices=DIFICULTAD_CHOICES)
    activa = models.BooleanField(default=True)
    creada_por = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='zonas_creadas',
        related_query_name='zona_creada',
    )
    actualizado_por = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='zonas_actualizadas',
        related_query_name='zona_actualizada',
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'zona'
        ordering = ['nivel', 'nombre']
        verbose_name = 'Zona'
        verbose_name_plural = 'Zonas'

    def __str__(self):
        return self.nombre


class Enemigo(models.Model):
    TIPO_CHOICES = (
        ('normal', 'Normal'),
        ('jefe', 'Jefe'),
    )

    RAREZA_CHOICES = (
        ('comun', 'Comun'),
        ('raro', 'Raro'),
        ('epico', 'Epico'),
        ('legendario', 'Legendario'),
    )

    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    zona = models.ForeignKey(
        Zona,
        on_delete=models.CASCADE,
        related_name='enemigos',
        related_query_name='enemigo',
    )
    rareza = models.CharField(max_length=20, choices=RAREZA_CHOICES)
    activo = models.BooleanField(default=True)
    creada_por = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='enemigos_creados',
        related_query_name='enemigo_creado',
    )
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

class Combate(models.Model):
    RESULTADO_CHOICES = (
        ('victoria', 'Victoria'),
        ('derrota', 'Derrota'),
        ('huida', 'Huida'),
    )

    TIPO_CHOICES = (
        ('normal', 'Normal'),
        ('jefe', 'Jefe'),
    )

    personaje = models.ForeignKey(
        Personaje,
        on_delete=models.CASCADE,
        related_name='combates',
        related_query_name='combate'
    )
    enemigo = models.ForeignKey(
        Enemigo,
        on_delete=models.CASCADE,
        related_name='combates',
        related_query_name='combate'
    )
    zona = models.ForeignKey(
        Zona,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='combates',
    )
    tipo = models.CharField(
        max_length=10, 
        choices=TIPO_CHOICES, 
        default='normal'
    )
    resultado = models.CharField(max_length=20, choices=RESULTADO_CHOICES, blank=True, null=True)
    exp_ganada = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    botin = models.ForeignKey(
        Objeto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='combates_dropeados'
    )
    fecha_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'juego_combate'
        verbose_name = 'Combate'
        verbose_name_plural = 'Combates'
        ordering = ['-fecha_hora']

        constraints = [
            models.CheckConstraint(
                condition=models.Q(exp_ganada__gte=0),
                name='exp_ganada_no_negativa'
            )
        ]

    def __str__(self):
        return f"{self.personaje.nombre} vs {self.enemigo.nombre} - {self.get_resultado_display()}"
