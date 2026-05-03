from django.db import models
from decimal import Decimal
from obras.models import Obra
from django.conf import settings


class EstadoPago(models.Model):

    ESTADO_CHOICES = [
        ('EN_GESTION', 'En Gestión'),
        ('ENVIADO', 'Enviado'),
        ('APROBADO', 'Aprobado'),
        ('RECHAZADO', 'Rechazado'),
        ('PAGADO', 'Pagado'),
    ]

    ESTADO_FIRMA_CHOICES = [
        ('PENDIENTE', 'Pendiente por Firmar'),
        ('PENDIENTE_EMPRESA', 'Pendiente Firma Empresa'),
        ('PENDIENTE_INSPECTOR', 'Pendiente Firma Inspector'),
        ('FIRMADA', 'Firmada'),
    ]

    obra = models.ForeignKey(
        Obra,
        on_delete=models.CASCADE,
        related_name='estados_pago'
    )

    numero_estado_pago = models.PositiveIntegerField()

    fecha_inicio_periodo = models.DateField()
    fecha_termino_periodo = models.DateField()

    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='EN_GESTION'
    )

    anticipo_descontado = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    monto_pagado_acumulado = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    saldo_restante_por_pagar = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    porcentaje_gastos_generales = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10
    )

    porcentaje_utilidades = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=8
    )

    tiene_anticipo = models.BooleanField(default=False)

    porcentaje_anticipo = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    porcentaje_devolucion_anticipo = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    estado_firma = models.CharField(
        max_length=30,
        choices=ESTADO_FIRMA_CHOICES,
        default='PENDIENTE'
        )

    firma_inspector_texto = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    firma_empresa_texto = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    firmado_inspector = models.BooleanField(default=False)
    firmado_empresa = models.BooleanField(default=False)

    fecha_firma_inspector = models.DateTimeField(blank=True, null=True)
    fecha_firma_empresa = models.DateTimeField(blank=True, null=True)

    usuario_firma_inspector = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='edps_firmados_como_inspector'
    )

    usuario_firma_empresa = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='edps_firmados_como_empresa'
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Estado de Pago'
        verbose_name_plural = 'Estados de Pago'
        ordering = ['numero_estado_pago']
        constraints = [
            models.UniqueConstraint(
                fields=['obra', 'numero_estado_pago'],
                name='unique_numero_edp_por_obra',
                violation_error_message='Ya existe un Estado de Pago con ese número para la obra seleccionada.'
            )
        ]
        
    def actualizar_estado_firma(self):
        if self.firmado_inspector and self.firmado_empresa:
            self.estado_firma = 'FIRMADA'
        elif self.firmado_inspector and not self.firmado_empresa:
            self.estado_firma = 'PENDIENTE_EMPRESA'
        elif self.firmado_empresa and not self.firmado_inspector:
            self.estado_firma = 'PENDIENTE_INSPECTOR'
        else:
            self.estado_firma = 'PENDIENTE'

    def __str__(self):
        return f'EDP {self.numero_estado_pago} - {self.obra.nombre}'

    @property
    def subtotal_periodo(self):
        return sum(
            (partida.monto_periodo for partida in self.partidas.all()),
            Decimal('0.00')
        )

    @property
    def gastos_generales(self):
        return self.subtotal_periodo * (self.porcentaje_gastos_generales / Decimal('100'))

    @property
    def utilidades(self):
        return self.subtotal_periodo * (self.porcentaje_utilidades / Decimal('100'))

    @property
    def neto(self):
        return self.subtotal_periodo + self.gastos_generales + self.utilidades

    @property
    def iva(self):
        return self.neto * Decimal('0.19')

    @property
    def total_general(self):
        return self.neto + self.iva

    @property
    def monto_contrato_base(self):
        return sum(
            (contrato.monto for contrato in self.obra.contratos.all()),
            Decimal('0.00')
        )

    @property
    def monto_anticipo_total(self):
        if not self.tiene_anticipo:
            return Decimal('0.00')

        return self.monto_contrato_base * (self.porcentaje_anticipo / Decimal('100'))

    @property
    def monto_descuento_anticipo(self):
        if not self.tiene_anticipo:
            return Decimal('0.00')

        return self.monto_anticipo_total * (self.porcentaje_devolucion_anticipo / Decimal('100'))

    @property
    def total_a_pagar_edp(self):
        total = self.total_general - self.monto_descuento_anticipo

        if total < Decimal('0.00'):
            return Decimal('0.00')

        return total


class PartidaEstadoPago(models.Model):

    TIPO_FILA_CHOICES = [
        ('TITULO', 'Título de Subpartida'),
        ('PARTIDA', 'Partida Valorizada'),
    ]

    estado_pago = models.ForeignKey(
        EstadoPago,
        on_delete=models.CASCADE,
        related_name='partidas'
    )

    tipo_fila = models.CharField(
        max_length=20,
        choices=TIPO_FILA_CHOICES,
        default='PARTIDA'
    )

    item = models.CharField(max_length=20)

    nombre_partida = models.CharField(max_length=255)

    unidad = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    cantidad = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    precio_unitario = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    porcentaje_avance_periodo = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    porcentaje_avance_acumulado = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    class Meta:
        verbose_name = 'Partida Estado de Pago'
        verbose_name_plural = 'Partidas Estado de Pago'
        ordering = ['item', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['estado_pago', 'item'],
                name='unique_item_por_estado_pago',
                violation_error_message='Ya existe una fila con ese ítem en esta planilla de partidas.'
            )
        ]

    def __str__(self):
        return f'{self.item} - {self.nombre_partida}'

    @property
    def monto_total_partida(self):
        if self.tipo_fila == 'TITULO':
            return Decimal('0.00')

        return self.cantidad * self.precio_unitario

    @property
    def porcentaje_pagado_acumulado(self):
        if self.tipo_fila == 'TITULO':
            return Decimal('0.00')

        partidas = PartidaEstadoPago.objects.filter(
            estado_pago__obra=self.estado_pago.obra,
            estado_pago__numero_estado_pago__lte=self.estado_pago.numero_estado_pago,
            item=self.item,
            tipo_fila='PARTIDA'
        )

        total = sum(
            (partida.porcentaje_avance_periodo for partida in partidas),
            Decimal('0.00')
        )

        if total > Decimal('100'):
            return Decimal('100.00')

        return total

    @property
    def monto_periodo(self):
        if self.tipo_fila == 'TITULO':
            return Decimal('0.00')

        return self.monto_total_partida * (self.porcentaje_avance_periodo / Decimal('100'))

    @property
    def monto_acumulado(self):
        if self.tipo_fila == 'TITULO':
            return Decimal('0.00')

        return self.monto_total_partida * (self.porcentaje_pagado_acumulado / Decimal('100'))

    @property
    def porcentaje_restante(self):
        if self.tipo_fila == 'TITULO':
            return Decimal('0.00')

        restante = Decimal('100.00') - self.porcentaje_pagado_acumulado

        if restante < Decimal('0.00'):
            return Decimal('0.00')

        return restante

    @property
    def saldo_restante(self):
        if self.tipo_fila == 'TITULO':
            return Decimal('0.00')

        return self.monto_total_partida * (self.porcentaje_restante / Decimal('100'))