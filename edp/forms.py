from decimal import Decimal, InvalidOperation
from django import forms
from .models import EstadoPago
from obras.models import Obra


def formatear_porcentaje_input(valor):
    if valor is None:
        return ''

    try:
        numero = Decimal(valor)

        if numero == numero.to_integral():
            return str(int(numero))

        return str(numero).replace(".", ",")

    except:
        return valor


def limpiar_porcentaje(valor):
    if valor in [None, '']:
        return Decimal('0')

    valor = str(valor).strip()
    valor = valor.replace(",", ".")

    try:
        return Decimal(valor)
    except InvalidOperation:
        return Decimal('0')


class EstadoPagoForm(forms.ModelForm):

    class Meta:
        model = EstadoPago
        fields = [
            'obra',
            'numero_estado_pago',
            'fecha_inicio_periodo',
            'estado',
            'porcentaje_gastos_generales',
            'porcentaje_utilidades',
            'tiene_anticipo',
            'porcentaje_anticipo',
            'porcentaje_devolucion_anticipo',
        ]

        widgets = {
            'obra': forms.Select(attrs={'class': 'form-select'}),

            'numero_estado_pago': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 1'
            }),

            'fecha_inicio_periodo': forms.DateInput(
                attrs={
                    'class': 'form-control',
                    'type': 'date'
                },
                format='%Y-%m-%d'
            ),

            'estado': forms.Select(attrs={'class': 'form-select'}),

            'porcentaje_gastos_generales': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 10'
            }),

            'porcentaje_utilidades': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 8'
            }),

            'tiene_anticipo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),

            'porcentaje_anticipo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 20'
            }),

            'porcentaje_devolucion_anticipo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 30'
            }),
        }

    def __init__(self, *args, **kwargs):
        inspector = kwargs.pop('inspector', None)

        super().__init__(*args, **kwargs)

        if inspector is not None:
            self.fields['obra'].queryset = Obra.objects.filter(
                inspector=inspector
            )

        self.fields['fecha_inicio_periodo'].input_formats = ['%Y-%m-%d']

        self.fields['tiene_anticipo'].required = False
        self.fields['porcentaje_anticipo'].required = False
        self.fields['porcentaje_devolucion_anticipo'].required = False

        numero_edp = None

        if self.data.get('numero_estado_pago'):
            try:
                numero_edp = int(self.data.get('numero_estado_pago'))
            except:
                pass

        elif self.instance and self.instance.pk:
            numero_edp = self.instance.numero_estado_pago

        if not self.instance.pk:
            self.initial['porcentaje_gastos_generales'] = ''
            self.initial['porcentaje_utilidades'] = ''
            self.initial['porcentaje_anticipo'] = ''
            self.initial['porcentaje_devolucion_anticipo'] = ''

        if self.instance and self.instance.pk:
            self.initial['porcentaje_gastos_generales'] = formatear_porcentaje_input(
                self.instance.porcentaje_gastos_generales
            )

            self.initial['porcentaje_utilidades'] = formatear_porcentaje_input(
                self.instance.porcentaje_utilidades
            )

            self.initial['porcentaje_anticipo'] = formatear_porcentaje_input(
                self.instance.porcentaje_anticipo
            )

            self.initial['porcentaje_devolucion_anticipo'] = formatear_porcentaje_input(
                self.instance.porcentaje_devolucion_anticipo
            )

        if numero_edp and numero_edp > 1:
            self.fields['tiene_anticipo'].widget = forms.HiddenInput()
            self.fields['porcentaje_anticipo'].widget.attrs['readonly'] = True

    def clean_porcentaje_gastos_generales(self):
        return limpiar_porcentaje(
            self.cleaned_data.get('porcentaje_gastos_generales')
        )

    def clean_porcentaje_utilidades(self):
        return limpiar_porcentaje(
            self.cleaned_data.get('porcentaje_utilidades')
        )

    def clean_porcentaje_anticipo(self):
        return limpiar_porcentaje(
            self.cleaned_data.get('porcentaje_anticipo')
        )

    def clean_porcentaje_devolucion_anticipo(self):
        return limpiar_porcentaje(
            self.cleaned_data.get('porcentaje_devolucion_anticipo')
        )

    def clean(self):
        cleaned_data = super().clean()

        numero_edp = cleaned_data.get('numero_estado_pago') or 1

        tiene_anticipo = cleaned_data.get('tiene_anticipo')
        porcentaje_anticipo = cleaned_data.get('porcentaje_anticipo') or Decimal('0')
        porcentaje_devolucion = cleaned_data.get(
            'porcentaje_devolucion_anticipo'
        ) or Decimal('0')

        if numero_edp > 1:
            return cleaned_data

        if not tiene_anticipo:
            cleaned_data['porcentaje_anticipo'] = Decimal('0')
            cleaned_data['porcentaje_devolucion_anticipo'] = Decimal('0')
            return cleaned_data

        if porcentaje_anticipo <= 0:
            self.add_error(
                'porcentaje_anticipo',
                'Debe ingresar el porcentaje de anticipo solicitado.'
            )

        if porcentaje_anticipo > 100:
            self.add_error(
                'porcentaje_anticipo',
                'El porcentaje de anticipo no puede superar el 100%.'
            )

        if porcentaje_devolucion < 0:
            self.add_error(
                'porcentaje_devolucion_anticipo',
                'El porcentaje de devolución no puede ser negativo.'
            )

        if porcentaje_devolucion > 100:
            self.add_error(
                'porcentaje_devolucion_anticipo',
                'La devolución del anticipo no puede superar el 100%.'
            )

        return cleaned_data