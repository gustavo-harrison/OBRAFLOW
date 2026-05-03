from django.db import models
from contratos.models import Contrato


class Garantia(models.Model):

    TIPO_GARANTIA_CHOICES = [
        ('FIEL_CUMPLIMIENTO', 'Fiel Correcto Cumplimiento de Contrato'),
        ('RESPONSABILIDAD_CIVIL', 'Responsabilidad Civil'),
        ('ANTICIPO', 'Anticipo'),
    ]

    contrato = models.ForeignKey(
        Contrato,
        on_delete=models.CASCADE,
        related_name='garantias'
    )

    tipo_garantia = models.CharField(
        max_length=30,
        choices=TIPO_GARANTIA_CHOICES
    )

    fecha_inicio_vigencia = models.DateField()

    fecha_termino_vigencia = models.DateField()

    observacion = models.TextField(
        blank=True,
        null=True
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Garantía'
        verbose_name_plural = 'Garantías'
        ordering = ['fecha_termino_vigencia']

    def __str__(self):
        return f'{self.get_tipo_garantia_display()} - {self.contrato.numero_contrato}'