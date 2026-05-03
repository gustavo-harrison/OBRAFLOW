from django.db import models
from django.conf import settings
from obras.models import Obra


class ConfiguracionActa(models.Model):
    nombre_mandante = models.CharField(max_length=255, blank=True, null=True)
    logo_mandante = models.ImageField(upload_to='actas/logos/', blank=True, null=True)

    class Meta:
        verbose_name = 'Configuración de Actas'
        verbose_name_plural = 'Configuración de Actas'

    def __str__(self):
        return self.nombre_mandante or 'Configuración de Actas'


class Acta(models.Model):

    TIPO_ACTA_CHOICES = [
        ('ENTREGA_TERRENO', 'Entrega de Terreno'),
        ('RECEPCION_OBS', 'Recepción con Observaciones'),
        ('RECEPCION_OK', 'Recepción sin Observaciones'),
    ]

    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente por Firmar'),
        ('PENDIENTE_EMPRESA', 'Pendiente Firma Empresa'),
        ('PENDIENTE_INSPECTOR', 'Pendiente Firma Inspector'),
        ('FIRMADA', 'Firmada'),
    ]

    obra = models.ForeignKey(
        Obra,
        on_delete=models.CASCADE,
        related_name='actas'
    )

    tipo_acta = models.CharField(
        max_length=30,
        choices=TIPO_ACTA_CHOICES
    )

    numero_acta = models.PositiveIntegerField()
    fecha_acta = models.DateField()

    titulo = models.CharField(max_length=255)
    cuerpo_acta = models.TextField()
    observaciones = models.TextField(blank=True, null=True)

    estado = models.CharField(
        max_length=30,
        choices=ESTADO_CHOICES,
        default='PENDIENTE'
    )

    # Datos autocompletados/editables
    nombre_obra = models.CharField(max_length=255)
    codigo_licitacion = models.CharField(max_length=100)
    nombre_empresa = models.CharField(max_length=255)
    rut_empresa = models.CharField(max_length=100, blank=True, null=True)
    nombre_inspector = models.CharField(max_length=255)
    ubicacion_obra = models.CharField(max_length=255, blank=True, null=True)

    # Firmas visibles en documento
    firma_inspector_texto = models.CharField(max_length=255)
    firma_empresa_texto = models.CharField(max_length=255)

    # Firma digital simple
    firmado_inspector = models.BooleanField(default=False)
    firmado_empresa = models.BooleanField(default=False)

    fecha_firma_inspector = models.DateTimeField(blank=True, null=True)
    fecha_firma_empresa = models.DateTimeField(blank=True, null=True)

    usuario_firma_inspector = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='actas_firmadas_como_inspector'
    )

    usuario_firma_empresa = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='actas_firmadas_como_empresa'
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Acta'
        verbose_name_plural = 'Actas'
        ordering = ['-fecha_acta', '-id']
        unique_together = ('obra', 'numero_acta')

    def actualizar_estado_firma(self):
        if self.firmado_inspector and self.firmado_empresa:
            self.estado = 'FIRMADA'
        elif self.firmado_inspector and not self.firmado_empresa:
            self.estado = 'PENDIENTE_EMPRESA'
        elif self.firmado_empresa and not self.firmado_inspector:
            self.estado = 'PENDIENTE_INSPECTOR'
        else:
            self.estado = 'PENDIENTE'

    def __str__(self):
        return f'Acta N° {self.numero_acta} - {self.get_tipo_acta_display()} - {self.nombre_obra}'