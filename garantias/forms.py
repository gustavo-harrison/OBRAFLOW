from django import forms
from .models import Garantia


class GarantiaForm(forms.ModelForm):
    class Meta:
        model = Garantia
        fields = [
            'tipo_garantia',
            'fecha_inicio_vigencia',
            'fecha_termino_vigencia',
            'observacion',
        ]

        widgets = {
            'tipo_garantia': forms.Select(attrs={
                'class': 'form-select'
            }),

            'fecha_inicio_vigencia': forms.DateInput(
                attrs={
                    'class': 'form-control',
                    'type': 'date'
                },
                format='%Y-%m-%d'
            ),

            'fecha_termino_vigencia': forms.DateInput(
                attrs={
                    'class': 'form-control',
                    'type': 'date'
                },
                format='%Y-%m-%d'
            ),

            'observacion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['fecha_inicio_vigencia'].input_formats = ['%Y-%m-%d']
        self.fields['fecha_termino_vigencia'].input_formats = ['%Y-%m-%d']