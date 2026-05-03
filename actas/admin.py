from django.contrib import admin
from .models import Acta, ConfiguracionActa


@admin.register(Acta)
class ActaAdmin(admin.ModelAdmin):
    list_display = (
        'numero_acta',
        'tipo_acta',
        'nombre_obra',
        'nombre_empresa',
        'fecha_acta',
        'estado',
    )
    search_fields = (
        'nombre_obra',
        'codigo_licitacion',
        'nombre_empresa',
        'nombre_inspector',
        'firma_empresa_texto',
    )
    list_filter = (
        'tipo_acta',
        'estado',
        'fecha_acta',
    )


@admin.register(ConfiguracionActa)
class ConfiguracionActaAdmin(admin.ModelAdmin):
    list_display = (
        'nombre_mandante',
        'logo_mandante',
    )