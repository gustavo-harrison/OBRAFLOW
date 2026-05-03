from django import forms
from .models import Contrato
from obras.models import Obra


class ContratoForm(forms.ModelForm):

    monto = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 12.000.000'
        })
    )

    class Meta:
        model = Contrato
        fields = [
            'obra',
            'numero_contrato',
            'tipo_contrato',
            'monto',
            'plazo_dias',
            'fecha_inicio',
            'fecha_termino',
            'estado',
        ]

        widgets = {
            'obra': forms.Select(attrs={'class': 'form-select'}),
            'numero_contrato': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: CT-001'}),
            'tipo_contrato': forms.Select(attrs={'class': 'form-select'}),
            'plazo_dias': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese valor númerico (Ej: 20, 60, 120)'}),
            'fecha_inicio': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d'
            ),
            'fecha_termino': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d'
            ),
            'estado': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        inspector = kwargs.pop('inspector', None)
        super().__init__(*args, **kwargs)

        if inspector:
            self.fields['obra'].queryset = Obra.objects.filter(inspector=inspector)

        self.fields['fecha_inicio'].input_formats = ['%Y-%m-%d']
        self.fields['fecha_termino'].input_formats = ['%Y-%m-%d']

        if self.instance and self.instance.pk and self.instance.monto:
            monto = int(self.instance.monto)
            self.initial['monto'] = f"{monto:,}".replace(",", ".")

    def validate_unique(self):
        pass

    def clean_numero_contrato(self):
        numero = self.cleaned_data.get('numero_contrato')
        return numero.strip() if numero else numero

    def clean_monto(self):
        monto = self.cleaned_data.get('monto', '')
        monto = str(monto).strip().replace(".", "").replace(",", "")

        if not monto.isdigit():
            raise forms.ValidationError('Ingrese un monto válido.')

        return int(monto)

