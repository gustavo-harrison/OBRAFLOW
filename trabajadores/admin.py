from django.contrib import admin
from .models import Trabajador, DocumentoTrabajador


class DocumentoTrabajadorInline(admin.StackedInline):
    model = DocumentoTrabajador
    extra = 0


@admin.register(Trabajador)
class TrabajadorAdmin(admin.ModelAdmin):
    list_display = (
        'nombres',
        'apellidos',
        'rut',
        'obra',
        'cargo',
        'estado',
        'fecha_ingreso',
    )
    search_fields = (
        'nombres',
        'apellidos',
        'rut',
        'obra__nombre',
        'obra__codigo',
    )
    list_filter = (
        'estado',
        'cargo',
        'fecha_ingreso',
    )
    inlines = [DocumentoTrabajadorInline]


@admin.register(DocumentoTrabajador)
class DocumentoTrabajadorAdmin(admin.ModelAdmin):
    list_display = (
        'trabajador',
        'carnet_identidad',
        'certificado_antecedentes',
        'contrato_trabajo',
        'fecha_actualizacion',
    )
    search_fields = (
        'trabajador__nombres',
        'trabajador__apellidos',
        'trabajador__rut',
    )