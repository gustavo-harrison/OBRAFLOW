from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator


class Obra(models.Model):

    rut_validator = RegexValidator(
        regex=r'^\d{1,2}\.\d{3}\.\d{3}-[\dkK]$',
        message='El RUT debe tener el formato xx.xxx.xxx-x'
    )

    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=200)

    descripcion = models.TextField(blank=True, null=True)
    ubicacion = models.CharField(max_length=255)

    CAMPUS_CHOICES = [
        ('CAMPUS_1', 'Campus Central'),
        ('CAMPUS_2', 'Campus Norte'),
        ('CAMPUS_3', 'Campus Sur'),
        ('CAMPUS_4', 'Campus Poniente'),
    ]

    campus = models.CharField(max_length=20, choices=CAMPUS_CHOICES)

    inspector = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='obras_como_inspector'
    )

    empresa = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='obras_como_empresa'
    )

    rut_empresa = models.CharField(
        max_length=12,
        validators=[rut_validator],
        blank=True,
        null=True
    )

    fecha_inicio = models.DateField()
    fecha_termino = models.DateField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    ESTADO_CHOICES = [
        ('PLANIFICACION', 'Planificación'),
        ('EN_PROCESO', 'En Ejecución'),
        ('FINALIZADA', 'Finalizada'),
    ]

    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='PLANIFICACION'
    )

    class Meta:
        verbose_name = 'Obra'
        verbose_name_plural = 'Obras'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"