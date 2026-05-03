from decimal import Decimal, InvalidOperation
from django import forms
from .models import PartidaEstadoPago, EstadoPago


def formatear_entero(valor):
    if valor is None:
        return ''

    try:
        numero = int(Decimal(valor))
        return str(numero)
    except:
        return valor


def formatear_clp_input(valor):
    if valor is None:
        return ''

    try:
        numero = int(Decimal(valor))
        return f"{numero:,}".replace(",", ".")
    except:
        return valor


def limpiar_numero(valor):
    if valor in [None, '']:
        return Decimal('0')

    valor = str(valor).strip()
    valor = valor.replace(".", "")
    valor = valor.replace(",", ".")

    try:
        return Decimal(valor)
    except InvalidOperation:
        return Decimal('0')


class PartidaEstadoPagoForm(forms.ModelForm):
    class Meta:
        model = PartidaEstadoPago
        fields = [
            'tipo_fila',
            'item',
            'nombre_partida',
            'unidad',
            'cantidad',
            'precio_unitario',
            'porcentaje_avance_periodo',
        ]

        widgets = {
            'tipo_fila': forms.Select(attrs={
                'class': 'form-select'
            }),

            'item': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 1, 1.1, 2.3'
            }),

            'nombre_partida': forms.TextInput(attrs={
                'class': 'form-control'
            }),

            'unidad': forms.TextInput(attrs={
                'class': 'form-control'
            }),

            'cantidad': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 100'
            }),

            'precio_unitario': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 5.500'
            }),

            'porcentaje_avance_periodo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 30'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.estado_pago = kwargs.pop('estado_pago', None)
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            self.estado_pago = self.instance.estado_pago
            self.initial['cantidad'] = formatear_entero(self.instance.cantidad)
            self.initial['precio_unitario'] = formatear_entero(self.instance.precio_unitario)
            self.initial['porcentaje_avance_periodo'] = formatear_entero(self.instance.porcentaje_avance_periodo)

    def clean_item(self):
        item = self.cleaned_data.get('item')
        return str(item).strip() if item else item

    def porcentaje_pagado_anterior(self, estado_pago, item):
        partidas_anteriores = PartidaEstadoPago.objects.filter(
            estado_pago__obra=estado_pago.obra,
            estado_pago__numero_estado_pago__lt=estado_pago.numero_estado_pago,
            item=item,
            tipo_fila='PARTIDA'
        )

        return sum(
            (partida.porcentaje_avance_periodo for partida in partidas_anteriores),
            Decimal('0.00')
        )

    def clean(self):
        cleaned_data = super().clean()

        tipo_fila = cleaned_data.get('tipo_fila')
        item = cleaned_data.get('item')
        porcentaje_periodo = cleaned_data.get('porcentaje_avance_periodo') or Decimal('0')

        estado_pago = self.estado_pago

        if not estado_pago and self.instance and self.instance.pk:
            estado_pago = self.instance.estado_pago

        if estado_pago and item:
            existe = PartidaEstadoPago.objects.filter(
                estado_pago=estado_pago,
                item=item
            ).exclude(pk=self.instance.pk).exists()

            if existe:
                raise forms.ValidationError(
                    'Ya existe una fila con ese ítem en esta planilla de partidas.'
                )

        if tipo_fila == 'TITULO':
            cleaned_data['unidad'] = ''
            cleaned_data['cantidad'] = Decimal('0')
            cleaned_data['precio_unitario'] = Decimal('0')
            cleaned_data['porcentaje_avance_periodo'] = Decimal('0')
            return cleaned_data

        if porcentaje_periodo < 0:
            self.add_error(
                'porcentaje_avance_periodo',
                'El % Presente EDP no puede ser negativo.'
            )

        if estado_pago and item:
            pagado_anterior = self.porcentaje_pagado_anterior(
                estado_pago,
                item
            )

            restante_disponible = Decimal('100.00') - pagado_anterior

            if restante_disponible < Decimal('0.00'):
                restante_disponible = Decimal('0.00')

            if porcentaje_periodo > restante_disponible:
                self.add_error(
                    'porcentaje_avance_periodo',
                    f'El % Presente EDP no puede superar el {restante_disponible:.0f}% restante disponible.'
                )

        return cleaned_data

    def clean_cantidad(self):
        return limpiar_numero(self.cleaned_data.get('cantidad'))

    def clean_precio_unitario(self):
        return limpiar_numero(self.cleaned_data.get('precio_unitario'))

    def clean_porcentaje_avance_periodo(self):
        return limpiar_numero(self.cleaned_data.get('porcentaje_avance_periodo'))