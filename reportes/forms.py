from django import forms
from obras.models import Obra


class ReporteObraForm(forms.Form):
    obra = forms.ModelChoiceField(
        queryset=Obra.objects.none(),
        label='Obra',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

    incluir_obra = forms.BooleanField(
        required=False,
        initial=False,
        label='Datos generales de la obra'
    )

    incluir_empresa = forms.BooleanField(
        required=False,
        initial=False,
        label='Empresa adjudicada'
    )

    incluir_contratos = forms.BooleanField(
        required=False,
        initial=False,
        label='Contratos'
    )

    incluir_garantias = forms.BooleanField(
        required=False,
        initial=False,
        label='Garantías'
    )

    incluir_edp = forms.BooleanField(
        required=False,
        initial=False,
        label='Estados de Pago'
    )

    incluir_trabajadores = forms.BooleanField(
        required=False,
        initial=False,
        label='Trabajadores'
    )

    incluir_actas = forms.BooleanField(
        required=False,
        initial=False,
        label='Actas'
    )

    def __init__(self, *args, **kwargs):
        inspector = kwargs.pop('inspector', None)
        super().__init__(*args, **kwargs)

        if inspector:
            self.fields['obra'].queryset = Obra.objects.filter(
                inspector=inspector
            ).order_by('nombre')

        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({
                    'class': 'form-check-input'
                })