from django import forms
from .models import Acta
from obras.models import Obra
import json


def nombre_completo_usuario(usuario):
    if not usuario:
        return ""

    nombre = f"{getattr(usuario, 'first_name', '')} {getattr(usuario, 'last_name', '')}".strip()

    if nombre:
        return nombre

    return getattr(usuario, 'username', '') or ""


def obtener_rut_empresa(obra):
    rut = (
        getattr(obra, 'rut_empresa', None)
        or getattr(obra, 'empresa_rut', None)
        or getattr(obra, 'rut_contratista', None)
        or getattr(obra, 'rut_empresa_contratista', None)
    )

    if rut:
        return rut

    empresa = getattr(obra, 'empresa', None)

    if empresa:
        rut_usuario = (
            getattr(empresa, 'rut', None)
            or getattr(empresa, 'rut_empresa', None)
            or getattr(empresa, 'documento', None)
        )

        if rut_usuario:
            return rut_usuario

    return ""


class ActaForm(forms.ModelForm):
    class Meta:
        model = Acta
        fields = [
            'obra',
            'tipo_acta',
            'numero_acta',
            'fecha_acta',
            'titulo',
            'cuerpo_acta',
            'observaciones',
            'estado',
            'nombre_obra',
            'codigo_licitacion',
            'nombre_empresa',
            'rut_empresa',
            'nombre_inspector',
            'ubicacion_obra',
            'firma_inspector_texto',
            'firma_empresa_texto',
        ]
        widgets = {
            'obra': forms.Select(attrs={'class': 'form-select', 'id': 'id_obra'}),
            'tipo_acta': forms.Select(attrs={'class': 'form-select', 'id': 'id_tipo_acta'}),
            'numero_acta': forms.NumberInput(attrs={'class': 'form-control'}),
            'fecha_acta': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'id': 'id_fecha_acta'}),
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_titulo'}),
            'cuerpo_acta': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'id': 'id_cuerpo_acta'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'nombre_obra': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_nombre_obra'}),
            'codigo_licitacion': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_codigo_licitacion'}),
            'nombre_empresa': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_nombre_empresa'}),
            'rut_empresa': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_rut_empresa'}),
            'nombre_inspector': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_nombre_inspector'}),
            'ubicacion_obra': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_ubicacion_obra'}),
            'firma_inspector_texto': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_firma_inspector_texto'}),
            'firma_empresa_texto': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_firma_empresa_texto'}),
        }

    def __init__(self, *args, **kwargs):
        inspector = kwargs.pop('inspector', None)
        super().__init__(*args, **kwargs)

        if inspector is not None:
            obras = Obra.objects.filter(inspector=inspector)
            self.fields['obra'].queryset = obras

            data = {}

            for obra in obras:
                empresa = getattr(obra, 'empresa', None)
                inspector_obra = getattr(obra, 'inspector', None)

                nombre_empresa = nombre_completo_usuario(empresa)
                nombre_inspector = nombre_completo_usuario(inspector_obra)

                data[str(obra.id)] = {
                    'nombre_obra': getattr(obra, 'nombre', '') or '',
                    'codigo_licitacion': getattr(obra, 'codigo', '') or '',
                    'nombre_empresa': nombre_empresa,
                    'rut_empresa': obtener_rut_empresa(obra),
                    'nombre_inspector': nombre_inspector,
                    'ubicacion_obra': getattr(obra, 'ubicacion', '') or '',
                    'firma_inspector_texto': nombre_inspector,
                    'firma_empresa_texto': '',
                }

            self.fields['obra'].widget.attrs['data-obras'] = json.dumps(data)