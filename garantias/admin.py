from django.contrib import admin
from .models import Garantia


@admin.register(Garantia)
class GarantiaAdmin(admin.ModelAdmin):
    list_display = (
        'tipo_garantia',
        'contrato',
        'fecha_inicio_vigencia',
        'fecha_termino_vigencia',
        'fecha_creacion',
    )
    search_fields = (
        'contrato__numero_contrato',
        'contrato__obra__nombre',
        'contrato__obra__codigo',
    )
    list_filter = (
        'tipo_garantia',
        'fecha_inicio_vigencia',
        'fecha_termino_vigencia',
    )
