from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404
from django.conf import settings

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader

import os

from obras.models import Obra
from contratos.models import Contrato
from garantias.models import Garantia
from edp.models import EstadoPago
from trabajadores.models import Trabajador
from actas.models import Acta, ConfiguracionActa
from .forms import ReporteObraForm


@login_required(login_url='login')
def reportes_index(request):
    if request.user.role != 'INSPECTOR':
        return HttpResponseForbidden('No tienes permiso para acceder a reportes.')

    form = ReporteObraForm(inspector=request.user)

    return render(request, 'reportes/index.html', {
        'form': form
    })


@login_required(login_url='login')
def reporte_obra_pdf(request):
    if request.user.role != 'INSPECTOR':
        return HttpResponseForbidden('No tienes permiso para generar reportes.')

    if request.method != 'POST':
        return HttpResponseForbidden('Método no permitido.')

    form = ReporteObraForm(request.POST, inspector=request.user)

    if not form.is_valid():
        return render(request, 'reportes/index.html', {
            'form': form
        })

    obra = get_object_or_404(
        Obra,
        id=form.cleaned_data['obra'].id,
        inspector=request.user
    )

    incluir_obra = form.cleaned_data['incluir_obra']
    incluir_empresa = form.cleaned_data['incluir_empresa']
    incluir_contratos = form.cleaned_data['incluir_contratos']
    incluir_garantias = form.cleaned_data['incluir_garantias']
    incluir_edp = form.cleaned_data['incluir_edp']
    incluir_trabajadores = form.cleaned_data['incluir_trabajadores']
    incluir_actas = form.cleaned_data['incluir_actas']

    contratos = Contrato.objects.filter(obra=obra)
    garantias = Garantia.objects.filter(contrato__obra=obra)
    edps = EstadoPago.objects.filter(obra=obra)
    trabajadores = Trabajador.objects.filter(obra=obra)
    actas = Acta.objects.filter(obra=obra)

    config_acta = ConfiguracionActa.objects.first()

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="reporte_obra_{obra.id}.pdf"'

    pdf = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    x_margin = 50
    content_width = width - (x_margin * 2)
    y_top = height - 50
    y_bottom = 70
    y = y_top - 95
    page_num = 1

    def nombre_usuario(usuario):
        if not usuario:
            return ""

        nombre = f"{getattr(usuario, 'first_name', '')} {getattr(usuario, 'last_name', '')}".strip()

        if nombre:
            return nombre

        return getattr(usuario, 'username', '') or ""

    def clp(valor):
        try:
            return f"${int(valor):,}".replace(",", ".")
        except Exception:
            return "$0"

    def fecha(valor):
        try:
            return valor.strftime("%d/%m/%Y")
        except Exception:
            return "-"

    def texto(valor):
        return str(valor) if valor not in [None, ""] else "-"

    def draw_header():
        pdf.setFont("Helvetica-Bold", 10)

        if config_acta and config_acta.nombre_mandante:
            pdf.drawString(x_margin, y_top, config_acta.nombre_mandante)
        else:
            pdf.drawString(x_margin, y_top, "OBRAFLOW")

        pdf.setFont("Helvetica", 8)
        pdf.setFillColor(colors.grey)
        pdf.drawString(x_margin, y_top - 13, "Reporte formal de obra")
        pdf.setFillColor(colors.black)

        logo_obraflow_path = os.path.join(
            settings.BASE_DIR,
            'static',
            'images',
            'logo_navbar.jpeg'
        )

        if os.path.exists(logo_obraflow_path):
            try:
                logo_obraflow = ImageReader(logo_obraflow_path)
                pdf.drawImage(
                    logo_obraflow,
                    width - 165,
                    y_top - 40,
                    width=115,
                    height=50,
                    preserveAspectRatio=True,
                    mask='auto'
                )
            except Exception:
                pass

    def draw_footer():
        pdf.setFont("Helvetica", 8)
        pdf.setFillColor(colors.grey)
        pdf.drawString(x_margin, 30, "Generado desde OBRAFLOW")
        pdf.drawRightString(width - x_margin, 30, f"Página {page_num}")
        pdf.setFillColor(colors.black)

    def new_page():
        nonlocal y, page_num
        draw_footer()
        pdf.showPage()
        page_num += 1
        draw_header()
        y = y_top - 70

    def ensure_space(space_needed=40):
        nonlocal y
        if y - space_needed < y_bottom:
            new_page()

    def draw_title():
        nonlocal y

        draw_header()

        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawCentredString(width / 2, y, "REPORTE RESUMEN DE OBRA")

        y -= 22
        pdf.setFont("Helvetica", 10)
        pdf.drawCentredString(width / 2, y, f"Obra: {obra.nombre}")

        y -= 14
        pdf.drawCentredString(width / 2, y, f"Código Licitación: {obra.codigo}")

        y -= 34

    def draw_section_title(title):
        nonlocal y

        ensure_space(35)

        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(x_margin, y, title)

        y -= 8
        pdf.setStrokeColor(colors.lightgrey)
        pdf.line(x_margin, y, width - x_margin, y)
        pdf.setStrokeColor(colors.black)

        y -= 18

    def draw_label_value(label, value, x=None, gap=16):
        nonlocal y

        ensure_space(gap + 5)

        if x is None:
            x = x_margin

        pdf.setFont("Helvetica-Bold", 9.5)
        pdf.drawString(x, y, f"{label}:")
        label_width = pdf.stringWidth(f"{label}: ", "Helvetica-Bold", 9.5)

        pdf.setFont("Helvetica", 9.5)
        pdf.drawString(x + label_width + 2, y, texto(value))

        y -= gap

    def draw_dual_label(left_label, left_value, right_label, right_value, gap=16):
        nonlocal y

        ensure_space(gap + 5)

        left_x = x_margin
        right_x = width / 2 + 10

        pdf.setFont("Helvetica-Bold", 9.5)
        pdf.drawString(left_x, y, f"{left_label}:")
        left_label_width = pdf.stringWidth(f"{left_label}: ", "Helvetica-Bold", 9.5)

        pdf.setFont("Helvetica", 9.5)
        pdf.drawString(left_x + left_label_width + 2, y, texto(left_value))

        pdf.setFont("Helvetica-Bold", 9.5)
        pdf.drawString(right_x, y, f"{right_label}:")
        right_label_width = pdf.stringWidth(f"{right_label}: ", "Helvetica-Bold", 9.5)

        pdf.setFont("Helvetica", 9.5)
        pdf.drawString(right_x + right_label_width + 2, y, texto(right_value))

        y -= gap

    def draw_item_box(title=None):
        nonlocal y

        ensure_space(28)

        if title:
            pdf.setFillColor(colors.Color(0.96, 0.96, 0.96))
            pdf.rect(x_margin, y - 4, content_width, 18, fill=1, stroke=0)
            pdf.setFillColor(colors.black)
            pdf.setFont("Helvetica-Bold", 9)
            pdf.drawString(x_margin + 8, y, title)
            y -= 22

    draw_title()

    if incluir_obra:
        draw_section_title("1. Datos Generales de la Obra")
        draw_dual_label("Nombre Obra", obra.nombre, "Código", obra.codigo)
        draw_dual_label(
            "Estado",
            obra.get_estado_display() if hasattr(obra, 'get_estado_display') else getattr(obra, 'estado', ''),
            "Ubicación",
            getattr(obra, 'ubicacion', '')
        )
        draw_dual_label("Fecha Inicio", fecha(getattr(obra, 'fecha_inicio', None)), "Fecha Término", fecha(getattr(obra, 'fecha_termino', None)))
        draw_label_value("Inspector", nombre_usuario(getattr(obra, 'inspector', None)))
        y -= 12

    if incluir_empresa:
        draw_section_title("2. Empresa Adjudicada")
        draw_dual_label("Empresa", nombre_usuario(getattr(obra, 'empresa', None)), "RUT Empresa", getattr(obra, 'rut_empresa', '') or getattr(obra, 'empresa_rut', ''))
        draw_label_value("Representante Legal", getattr(obra, 'representante_legal', ''))
        y -= 12

    if incluir_contratos:
        draw_section_title("3. Contratos")

        if contratos.exists():
            for contrato in contratos:
                draw_item_box(f"Contrato {getattr(contrato, 'numero_contrato', '') or getattr(contrato, 'numero_resolucion', '') or ''}")
                draw_dual_label("N° Contrato", getattr(contrato, 'numero_contrato', ''), "Tipo", getattr(contrato, 'get_tipo_contrato_display', lambda: getattr(contrato, 'tipo_contrato', ''))())
                draw_dual_label("Monto", clp(getattr(contrato, 'monto', 0)), "Plazo", f"{getattr(contrato, 'plazo_dias', '')} días")
                draw_dual_label("Fecha Inicio", fecha(getattr(contrato, 'fecha_inicio', None)), "Fecha Término", fecha(getattr(contrato, 'fecha_termino', None)))
                y -= 8
        else:
            draw_label_value("Información", "No existen contratos asociados.")

        y -= 12

    if incluir_garantias:
        draw_section_title("4. Garantías")

        if garantias.exists():
            for garantia in garantias:
                tipo_garantia = getattr(
                    garantia,
                    'get_tipo_garantia_display',
                    lambda: getattr(garantia, 'tipo_garantia', '')
                )()

                draw_item_box(tipo_garantia)
                draw_dual_label("Tipo", tipo_garantia, "Entidad", getattr(garantia, 'entidad_emisora', ''))
                draw_dual_label("Fecha Inicio", fecha(getattr(garantia, 'fecha_inicio_vigencia', None)), "Fecha Término", fecha(getattr(garantia, 'fecha_termino_vigencia', None)))
                draw_label_value("Monto", clp(getattr(garantia, 'monto', 0)))
                y -= 8
        else:
            draw_label_value("Información", "No existen garantías asociadas.")

        y -= 12

    if incluir_edp:
        draw_section_title("5. Estados de Pago")

        if edps.exists():
            for edp in edps:
                draw_item_box(f"Estado de Pago N° {edp.numero_estado_pago}")
                draw_dual_label("Período Inicio", fecha(edp.fecha_inicio_periodo), "Período Término", fecha(edp.fecha_termino_periodo))
                draw_dual_label("Estado", edp.get_estado_display(), "Estado Firma", edp.get_estado_firma_display())
                draw_dual_label("Total General", clp(edp.total_general), "Total a Pagar", clp(edp.total_a_pagar_edp))
                draw_label_value("Descuento Anticipo", clp(edp.monto_descuento_anticipo))
                y -= 8
        else:
            draw_label_value("Información", "No existen estados de pago asociados.")

        y -= 12

    if incluir_trabajadores:
        draw_section_title("6. Trabajadores")

        if trabajadores.exists():
            for trabajador in trabajadores:
                nombre_trabajador = f"{trabajador.nombres} {trabajador.apellidos}".strip()
                draw_item_box(nombre_trabajador)
                draw_dual_label("Nombre", nombre_trabajador, "RUT", trabajador.rut)
                draw_dual_label("Cargo", trabajador.cargo, "Estado", trabajador.get_estado_display())
                y -= 8
        else:
            draw_label_value("Información", "No existen trabajadores asociados.")

        y -= 12

    if incluir_actas:
        draw_section_title("7. Actas")

        if actas.exists():
            for acta in actas:
                draw_item_box(f"Acta N° {acta.numero_acta}")
                draw_dual_label("Tipo", acta.get_tipo_acta_display(), "Fecha", fecha(acta.fecha_acta))
                draw_dual_label("Estado", acta.get_estado_display(), "Obra", acta.nombre_obra)
                y -= 8
        else:
            draw_label_value("Información", "No existen actas asociadas.")

        y -= 12

    draw_footer()
    pdf.save()
    return response