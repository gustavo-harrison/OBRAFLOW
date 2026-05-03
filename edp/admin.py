from django.contrib import admin
from .models import EstadoPago, PartidaEstadoPago


@admin.register(EstadoPago)
class EstadoPagoAdmin(admin.ModelAdmin):
    list_display = (
        'numero_estado_pago',
        'obra',
        'estado',
        'fecha_inicio_periodo',
        'fecha_termino_periodo',
    )

    search_fields = (
        'obra__nombre',
        'obra__codigo',
        'numero_estado_pago',
    )

    list_filter = (
        'estado',
        'obra',
    )


@admin.register(PartidaEstadoPago)
class PartidaEstadoPagoAdmin(admin.ModelAdmin):
    list_display = (
        'estado_pago',
        'item',
        'tipo_fila',
        'nombre_partida',
        'unidad',
        'cantidad',
        'precio_unitario',
    )

    search_fields = (
        'item',
        'nombre_partida',
        'estado_pago__obra__nombre',
    )

    list_filter = (
        'tipo_fila',
        'estado_pago',
    )