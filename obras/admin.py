from django.contrib import admin
from .models import Obra


@admin.register(Obra)
class ObraAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'campus', 'inspector', 'empresa', 'estado')
    search_fields = ('codigo', 'nombre')
    list_filter = ('campus', 'estado')