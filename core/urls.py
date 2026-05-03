from django.urls import path
from .views import (
    index,
    login_view,
    logout_view,
    dashboard_redirect,
    dashboard_inspector,
    dashboard_empresa,

    obras_lista,
    obras_detalle,
    obras_crear,
    obras_editar,
    obras_eliminar,

    contratos_lista,
    contratos_detalle,
    contratos_crear,
    contratos_editar,
    contratos_eliminar,

    garantia_crear,
    garantia_editar,
    garantia_eliminar,

    edp_lista,
    edp_detalle,
    edp_crear,
    edp_editar,
    edp_eliminar,
    edp_pdf,
    firmar_edp,

    partida_edp_crear,
    partida_edp_editar,
    partida_edp_eliminar,

    trabajadores_lista,
    trabajadores_detalle,
    trabajadores_crear,
    trabajadores_editar,
    trabajadores_eliminar,
    trabajador_documentos_editar,

    documentos_lista,
    documentos_detalle,
    documentos_subir,

    actas_lista,
    actas_detalle,
    actas_crear,
    actas_editar,
    actas_eliminar,
    firmar_acta,
    actas_pdf,

    perfil_usuario,
    cambiar_password,

)

urlpatterns = [
    path('', index, name='index'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),

    path('perfil/', perfil_usuario, name='perfil_usuario'),
    path('perfil/cambiar-password/', cambiar_password, name='cambiar_password'),

    path('dashboard/', dashboard_redirect, name='dashboard'),
    path('dashboard/inspector/', dashboard_inspector, name='dashboard_inspector'),
    path('dashboard/empresa/', dashboard_empresa, name='dashboard_empresa'),

    path('obras/', obras_lista, name='obras'),
    path('obras/crear/', obras_crear, name='obras_crear'),
    path('obras/<int:obra_id>/', obras_detalle, name='obras_detalle'),
    path('obras/<int:obra_id>/editar/', obras_editar, name='obras_editar'),
    path('obras/<int:obra_id>/eliminar/', obras_eliminar, name='obras_eliminar'),

    path('contratos/', contratos_lista, name='contratos'),
    path('contratos/crear/', contratos_crear, name='contratos_crear'),
    path('contratos/<int:contrato_id>/', contratos_detalle, name='contratos_detalle'),
    path('contratos/<int:contrato_id>/editar/', contratos_editar, name='contratos_editar'),
    path('contratos/<int:contrato_id>/eliminar/', contratos_eliminar, name='contratos_eliminar'),

    path('contratos/<int:contrato_id>/garantias/crear/', garantia_crear, name='garantia_crear'),
    path('garantias/<int:garantia_id>/editar/', garantia_editar, name='garantia_editar'),
    path('garantias/<int:garantia_id>/eliminar/', garantia_eliminar, name='garantia_eliminar'),

    path('edp/', edp_lista, name='edp'),
    path('edp/crear/', edp_crear, name='edp_crear'),
    path('edp/<int:edp_id>/', edp_detalle, name='edp_detalle'),
    path('edp/<int:edp_id>/editar/', edp_editar, name='edp_editar'),
    path('edp/<int:edp_id>/eliminar/', edp_eliminar, name='edp_eliminar'),
    path('edp/<int:edp_id>/firmar/', firmar_edp, name='firmar_edp'),
    path('edp/<int:edp_id>/pdf/', edp_pdf, name='edp_pdf'),

    path('edp/<int:edp_id>/partidas/crear/', partida_edp_crear, name='partida_edp_crear'),
    path('edp/partidas/<int:partida_id>/editar/', partida_edp_editar, name='partida_edp_editar'),
    path('edp/partidas/<int:partida_id>/eliminar/', partida_edp_eliminar, name='partida_edp_eliminar'),

    path('trabajadores/', trabajadores_lista, name='trabajadores'),
    path('trabajadores/crear/', trabajadores_crear, name='trabajadores_crear'),
    path('trabajadores/<int:trabajador_id>/', trabajadores_detalle, name='trabajadores_detalle'),
    path('trabajadores/<int:trabajador_id>/editar/', trabajadores_editar, name='trabajadores_editar'),
    path('trabajadores/<int:trabajador_id>/eliminar/', trabajadores_eliminar, name='trabajadores_eliminar'),
    path('trabajadores/<int:trabajador_id>/documentos/', trabajador_documentos_editar, name='trabajador_documentos_editar'),

    path('documentos/', documentos_lista, name='documentos'),
    path('documentos/<int:documento_id>/', documentos_detalle, name='documentos_detalle'),
    path('documentos/subir/', documentos_subir, name='documentos_subir'),

    path('actas/', actas_lista, name='actas'),
    path('actas/crear/', actas_crear, name='actas_crear'),
    path('actas/<int:acta_id>/', actas_detalle, name='actas_detalle'),
    path('actas/<int:acta_id>/editar/', actas_editar, name='actas_editar'),
    path('actas/<int:acta_id>/eliminar/', actas_eliminar, name='actas_eliminar'),
    path('actas/<int:acta_id>/firmar/', firmar_acta, name='firmar_acta'),
    path('actas/<int:acta_id>/pdf/', actas_pdf, name='actas_pdf'),

]