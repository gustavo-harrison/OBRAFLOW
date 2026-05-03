from django.urls import path
from .views import reportes_index, reporte_obra_pdf

urlpatterns = [
    path('', reportes_index, name='reportes_index'),
    path('generar-pdf/', reporte_obra_pdf, name='reporte_obra_pdf'),
]