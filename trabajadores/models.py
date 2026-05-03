from django.db import models
from obras.models import Obra


class Trabajador(models.Model):
    ESTADO_CHOICES = [
        ('ACTIVO', 'Activo'),
        ('INACTIVO', 'Inactivo'),
    ]

    obra = models.ForeignKey(
        Obra,
        on_delete=models.CASCADE,
        related_name='trabajadores'
    )

    nombres = models.CharField(max_length=150)
    apellidos = models.CharField(max_length=150)
    rut = models.CharField(max_length=20)
    fecha_nacimiento = models.DateField()
    cargo = models.CharField(max_length=150)
    fecha_ingreso = models.DateField()

    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='ACTIVO'
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Trabajador'
        verbose_name_plural = 'Trabajadores'
        ordering = ['apellidos', 'nombres']

    def __str__(self):
        return f'{self.nombres} {self.apellidos} - {self.rut}'

    @property
    def documentos_completos(self):
        return hasattr(self, 'documentos') and all([
            self.documentos.carnet_identidad,
            self.documentos.certificado_antecedentes,
            self.documentos.contrato_trabajo,
        ])


class DocumentoTrabajador(models.Model):
    trabajador = models.OneToOneField(
        Trabajador,
        on_delete=models.CASCADE,
        related_name='documentos'
    )

    carnet_identidad = models.FileField(
        upload_to='trabajadores/carnet/',
        blank=True,
        null=True
    )

    certificado_antecedentes = models.FileField(
        upload_to='trabajadores/antecedentes/',
        blank=True,
        null=True
    )

    contrato_trabajo = models.FileField(
        upload_to='trabajadores/contratos/',
        blank=True,
        null=True
    )

    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Documento de Trabajador'
        verbose_name_plural = 'Documentos de Trabajadores'

    def __str__(self):
        return f'Documentos - {self.trabajador.nombres} {self.trabajador.apellidos}'