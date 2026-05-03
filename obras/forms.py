from django import forms
from django.contrib.auth import get_user_model
from .models import Obra

User = get_user_model()


class EmpresaModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        nombre_completo = f"{obj.first_name} {obj.last_name}".strip()

        if nombre_completo:
            return nombre_completo

        return obj.username


class ObraForm(forms.ModelForm):
    empresa = EmpresaModelChoiceField(
        queryset=User.objects.filter(role='CONTRATISTA'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Obra
        fields = [
            'codigo',
            'nombre',
            'descripcion',
            'ubicacion',
            'campus',
            'empresa',
            'rut_empresa',
            'fecha_inicio',
            'fecha_termino',
            'estado',
        ]

        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: LIC-001'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Construcción edificio administrativo'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe brevemente el alcance de la obra'
            }),
            'ubicacion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Santiago, Región Metropolitana'
            }),
            'campus': forms.Select(attrs={
                'class': 'form-select'
            }),
            'rut_empresa': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 12.345.678-9'
            }),
            'fecha_inicio': forms.DateInput(
                attrs={
                    'class': 'form-control',
                    'type': 'date'
                },
                format='%Y-%m-%d'
            ),
            'fecha_termino': forms.DateInput(
                attrs={
                    'class': 'form-control',
                    'type': 'date'
                },
                format='%Y-%m-%d'
            ),
            'estado': forms.Select(attrs={
                'class': 'form-select'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['empresa'].queryset = User.objects.filter(role='CONTRATISTA')
        self.fields['descripcion'].required = False
        self.fields['fecha_termino'].required = False
        self.fields['rut_empresa'].required = False

        self.fields['fecha_inicio'].input_formats = ['%Y-%m-%d']
        self.fields['fecha_termino'].input_formats = ['%Y-%m-%d']