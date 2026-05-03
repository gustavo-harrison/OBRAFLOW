from django.db import models
from obras.models import Obra


class Contrato(models.Model):

    TIPO_CONTRATO_CHOICES = [
        ('PRIMITIVO', 'Primitivo'),
        ('ADENDUM', 'Adendum'),
    ]

    ESTADO_CHOICES = [
        ('VIGENTE', 'Vigente'),
        ('FINALIZADO', 'Finalizado'),
        ('SUSPENDIDO', 'Suspendido'),
    ]

    obra = models.ForeignKey(
        Obra,
        on_delete=models.CASCADE,
        related_name='contratos'
    )

    numero_contrato = models.CharField(
        max_length=100
    )

    tipo_contrato = models.CharField(
        max_length=20,
        choices=TIPO_CONTRATO_CHOICES,
        default='PRIMITIVO'
    )

    monto = models.DecimalField(
        max_digits=14,
        decimal_places=2
    )

    plazo_dias = models.PositiveIntegerField()

    fecha_inicio = models.DateField()

    fecha_termino = models.DateField()

    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='VIGENTE'
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Contrato'
        verbose_name_plural = 'Contratos'
        ordering = ['-fecha_creacion']
        constraints = [
            models.UniqueConstraint(
                fields=['obra', 'numero_contrato'],
                name='unique_numero_contrato_por_obra',
                violation_error_message='Ya existe un contrato con ese número para la obra seleccionada.'
            )
        ]

    def __str__(self):
        return f'{self.numero_contrato} - {self.obra.nombre}'