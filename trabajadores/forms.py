from django import forms
from .models import Trabajador, DocumentoTrabajador
from obras.models import Obra


class TrabajadorForm(forms.ModelForm):
    class Meta:
        model = Trabajador
        fields = [
            'obra',
            'nombres',
            'apellidos',
            'rut',
            'fecha_nacimiento',
            'cargo',
            'fecha_ingreso',
            'estado',
        ]
        widgets = {
            'obra': forms.Select(attrs={'class': 'form-select'}),
            'nombres': forms.TextInput(attrs={'class': 'form-control'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control'}),
            'rut': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_nacimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'cargo': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_ingreso': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)

        if empresa is not None:
            self.fields['obra'].queryset = Obra.objects.filter(empresa=empresa)


class DocumentoTrabajadorForm(forms.ModelForm):
    class Meta:
        model = DocumentoTrabajador
        fields = [
            'carnet_identidad',
            'certificado_antecedentes',
            'contrato_trabajo',
        ]
        widgets = {
            'carnet_identidad': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'certificado_antecedentes': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'contrato_trabajo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }