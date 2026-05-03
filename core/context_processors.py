from datetime import timedelta
from django.utils import timezone

from garantias.models import Garantia
from edp.models import EstadoPago
from trabajadores.models import Trabajador
from actas.models import Acta


def nombre_usuario(usuario):
    if not usuario:
        return ""

    nombre = f"{getattr(usuario, 'first_name', '')} {getattr(usuario, 'last_name', '')}".strip()

    if nombre:
        return nombre

    return getattr(usuario, 'username', '') or ""


def alertas_inspector(request):
    if not request.user.is_authenticated:
        return {}

    hoy = timezone.localdate()
    limite_10_dias = hoy + timedelta(days=10)

    # =========================
    # ALERTAS INSPECTOR
    # =========================
    if getattr(request.user, 'role', None) == 'INSPECTOR':
        garantias = Garantia.objects.filter(contrato__obra__inspector=request.user)
        trabajadores = Trabajador.objects.filter(obra__inspector=request.user)
        edps = EstadoPago.objects.filter(obra__inspector=request.user)
        actas = Acta.objects.filter(obra__inspector=request.user)

        garantias_por_vencer = []

        for garantia in garantias:
            fecha_vencimiento = (
                getattr(garantia, 'fecha_termino_vigencia', None)
                or getattr(garantia, 'fecha_fin', None)
                or getattr(garantia, 'fecha_vencimiento', None)
            )

            if fecha_vencimiento and hoy <= fecha_vencimiento <= limite_10_dias:
                garantias_por_vencer.append(garantia)

        actas_pendientes_firma = actas.exclude(
            estado='FIRMADA'
        )

        edps_pendientes = edps.exclude(
            estado='PAGADO'
        )

        trabajadores_documentos_pendientes = [
            trabajador for trabajador in trabajadores
            if not trabajador.documentos_completos
        ]

        trabajadores_agrupados_dict = {}

        for trabajador in trabajadores_documentos_pendientes:
            obra = trabajador.obra
            empresa = obra.empresa if obra else None

            key = obra.id if obra else trabajador.id

            if key not in trabajadores_agrupados_dict:
                trabajadores_agrupados_dict[key] = {
                    'obra_id': obra.id if obra else None,
                    'obra_nombre': obra.nombre if obra else 'Sin obra',
                    'empresa_nombre': nombre_usuario(empresa),
                    'cantidad_pendiente': 0,
                }

            trabajadores_agrupados_dict[key]['cantidad_pendiente'] += 1

        trabajadores_pendientes_agrupados = list(trabajadores_agrupados_dict.values())

        total_alertas = (
            len(garantias_por_vencer)
            + actas_pendientes_firma.count()
            + edps_pendientes.count()
            + len(trabajadores_documentos_pendientes)
        )

        return {
            'nav_total_alertas': total_alertas,

            'nav_garantias_por_vencer_count': len(garantias_por_vencer),
            'nav_actas_pendientes_count': actas_pendientes_firma.count(),
            'nav_edps_pendientes_count': edps_pendientes.count(),
            'nav_trabajadores_docs_pendientes_count': len(trabajadores_documentos_pendientes),

            'nav_garantias_por_vencer': garantias_por_vencer[:5],
            'nav_actas_pendientes': actas_pendientes_firma[:5],
            'nav_edps_pendientes': edps_pendientes[:5],
            'nav_trabajadores_pendientes_agrupados': trabajadores_pendientes_agrupados[:5],
        }

    # =========================
    # ALERTAS EMPRESA
    # =========================
    if getattr(request.user, 'role', None) == 'CONTRATISTA':
        trabajadores = Trabajador.objects.filter(obra__empresa=request.user)
        actas = Acta.objects.filter(obra__empresa=request.user)
        edps = EstadoPago.objects.filter(obra__empresa=request.user)

        trabajadores_documentos_pendientes = [
            trabajador for trabajador in trabajadores
            if not trabajador.documentos_completos
        ]

        documentos_pendientes_firma = actas.exclude(
            estado='FIRMADA'
        )

        edps_revision = edps.exclude(
            estado='PAGADO'
        )

        total_alertas_empresa = (
            len(trabajadores_documentos_pendientes)
            + documentos_pendientes_firma.count()
            + edps_revision.count()
        )

        return {
            'nav_total_alertas_empresa': total_alertas_empresa,

            'nav_empresa_trabajadores_docs_pendientes_count': len(trabajadores_documentos_pendientes),
            'nav_empresa_documentos_pendientes_count': documentos_pendientes_firma.count(),
            'nav_empresa_edps_revision_count': edps_revision.count(),

            'nav_empresa_trabajadores_docs_pendientes': trabajadores_documentos_pendientes[:5],
            'nav_empresa_documentos_pendientes': documentos_pendientes_firma[:5],
            'nav_empresa_edps_revision': edps_revision[:5],
        }

    return {}