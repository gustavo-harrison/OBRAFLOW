from django.contrib import admin
from .models import Contrato


@admin.register(Contrato)
class ContratoAdmin(admin.ModelAdmin):
    list_display = (
        'numero_contrato',
        'obra',
        'tipo_contrato',
        'monto',
        'plazo_dias',
        'estado',
        'fecha_inicio',
        'fecha_termino',
    )
    search_fields = (
        'numero_contrato',
        'obra__nombre',
        'obra__codigo',
    )
    list_filter = (
        'tipo_contrato',
        'estado',
        'fecha_inicio',
        'fecha_termino',
    )
