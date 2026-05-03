from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, HttpResponse
from django.db.models import Q
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from datetime import timedelta

from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
import os

from obras.models import Obra
from obras.forms import ObraForm

from contratos.models import Contrato
from contratos.forms import ContratoForm

from garantias.models import Garantia
from garantias.forms import GarantiaForm

from edp.models import EstadoPago, PartidaEstadoPago
from edp.forms import EstadoPagoForm
from edp.forms_partidas import PartidaEstadoPagoForm

from actas.models import Acta, ConfiguracionActa
from actas.forms import ActaForm

from trabajadores.models import Trabajador, DocumentoTrabajador
from trabajadores.forms import TrabajadorForm, DocumentoTrabajadorForm

from django.contrib.auth import update_session_auth_hash
from users.forms import PerfilUsuarioForm, CambiarPasswordForm


# =========================
# VISTAS PÚBLICAS
# =========================

def index(request):
    return render(request, 'index.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            if user.role == 'ADMIN' or user.is_superuser:
                return redirect('/admin/')

            return redirect('dashboard')
        else:
            return render(request, 'login.html', {
                'error': 'Usuario o contraseña incorrectos'
            })

    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('index')


# =========================
# DASHBOARDS
# =========================

@login_required(login_url='login')
def dashboard_redirect(request):
    if request.user.role == 'ADMIN' or request.user.is_superuser:
        return redirect('/admin/')

    if request.user.role == 'INSPECTOR':
        return redirect('dashboard_inspector')

    elif request.user.role == 'CONTRATISTA':
        return redirect('dashboard_empresa')

    return redirect('index')


@login_required(login_url='login')
def dashboard_inspector(request):
    hoy = timezone.localdate()
    limite_10_dias = hoy + timedelta(days=10)

    obras = Obra.objects.filter(inspector=request.user)
    contratos = Contrato.objects.filter(obra__inspector=request.user)
    edps = EstadoPago.objects.filter(obra__inspector=request.user)
    actas = Acta.objects.filter(obra__inspector=request.user)
    garantias = Garantia.objects.filter(contrato__obra__inspector=request.user)

    garantias_por_vencer = []
    garantias_vencidas = []

    for garantia in garantias:
        fecha_vencimiento = (
            getattr(garantia, 'fecha_termino_vigencia', None)
            or getattr(garantia, 'fecha_fin', None)
            or getattr(garantia, 'fecha_vencimiento', None)
        )

        if fecha_vencimiento:
            if fecha_vencimiento < hoy:
                garantias_vencidas.append(garantia)
            elif hoy <= fecha_vencimiento <= limite_10_dias:
                garantias_por_vencer.append(garantia)

    context = {
        'total_obras': obras.count(),
        'total_contratos': contratos.count(),
        'total_edps': edps.count(),
        'total_actas': actas.count(),
        'total_garantias': garantias.count(),

        'edp_borrador': edps.filter(estado='EN_GESTION').count(),
        'edp_enviado': edps.filter(estado='ENVIADO').count(),
        'edp_aprobado': edps.filter(estado='APROBADO').count(),
        'edp_pagado': edps.filter(estado='PAGADO').count(),

        'actas_pendientes': actas.exclude(estado='FIRMADA').count(),
        'actas_firmadas': actas.filter(estado='FIRMADA').count(),

        'garantias_por_vencer': len(garantias_por_vencer),
        'garantias_vencidas': len(garantias_vencidas),
        'garantias_vigentes': garantias.count() - len(garantias_vencidas),
    }

    return render(request, 'dashboard_inspector.html', context)

@login_required(login_url='login')
def dashboard_empresa(request):
    obras = Obra.objects.filter(empresa=request.user)
    trabajadores = Trabajador.objects.filter(obra__empresa=request.user)
    actas = Acta.objects.filter(obra__empresa=request.user)
    edps = EstadoPago.objects.filter(obra__empresa=request.user)

    trabajadores_docs_pendientes = [
        trabajador for trabajador in trabajadores
        if not trabajador.documentos_completos
    ]

    context = {
        'total_obras': obras.count(),
        'total_trabajadores': trabajadores.count(),
        'total_documentos': actas.count(),

        'trabajadores_activos': trabajadores.filter(estado='ACTIVO').count(),
        'trabajadores_inactivos': trabajadores.filter(estado='INACTIVO').count(),
        'trabajadores_docs_pendientes': len(trabajadores_docs_pendientes),

        # ACTAS
        'documentos_pendientes': actas.exclude(estado='FIRMADA').count(),
        'documentos_firmados': actas.filter(estado='FIRMADA').count(),

        # EDP - Vista Empresa
        'edp_pendientes': edps.exclude(estado='PAGADO').exclude(estado_firma='FIRMADA').count(),
        'edp_firmados': edps.filter(estado_firma='FIRMADA').exclude(estado='PAGADO').count(),
        'edp_pagados': edps.filter(estado='PAGADO').count(),
    }

    return render(request, 'dashboard_empresa.html', context)


# =========================
# OBRAS
# =========================

@login_required(login_url='login')
def obras_lista(request):
    user = request.user

    if user.role == 'INSPECTOR':
        obras = Obra.objects.filter(inspector=user)
    elif user.role == 'CONTRATISTA':
        obras = Obra.objects.filter(empresa=user)
    else:
        obras = Obra.objects.none()

    busqueda = request.GET.get('q', '').strip()
    campus = request.GET.get('campus', '').strip()
    estado = request.GET.get('estado', '').strip()

    if busqueda:
        obras = obras.filter(
            Q(codigo__icontains=busqueda) |
            Q(nombre__icontains=busqueda)
        )

    if campus:
        obras = obras.filter(campus=campus)

    if estado:
        obras = obras.filter(estado=estado)

    filtros_activos = 0
    if busqueda:
        filtros_activos += 1
    if campus:
        filtros_activos += 1
    if estado:
        filtros_activos += 1

    context = {
        'obras': obras,
        'busqueda': busqueda,
        'campus_actual': campus,
        'estado_actual': estado,
        'campus_choices': Obra.CAMPUS_CHOICES,
        'estado_choices': Obra.ESTADO_CHOICES,
        'filtros_activos': filtros_activos,
    }

    return render(request, 'obras/lista.html', context)


@login_required(login_url='login')
def obras_detalle(request, obra_id):
    user = request.user

    if user.role == 'INSPECTOR':
        obra = get_object_or_404(
            Obra,
            id=obra_id,
            inspector=user
        )
    elif user.role == 'CONTRATISTA':
        obra = get_object_or_404(
            Obra,
            id=obra_id,
            empresa=user
        )
    else:
        return HttpResponseForbidden('No tienes permiso para ver esta obra.')

    contratos = obra.contratos.all()
    garantias = Garantia.objects.filter(contrato__obra=obra)
    trabajadores = obra.trabajadores.all()

    return render(request, 'obras/detalle.html', {
        'obra': obra,
        'contratos': contratos,
        'garantias': garantias,
        'trabajadores': trabajadores,
    })


@login_required(login_url='login')
def obras_crear(request):
    if request.user.role != 'INSPECTOR':
        return HttpResponseForbidden('No tienes permiso para crear obras.')

    if request.method == 'POST':
        form = ObraForm(request.POST)
        if form.is_valid():
            obra = form.save(commit=False)
            obra.inspector = request.user
            obra.save()
            messages.success(request, f'La obra "{obra.nombre}" fue creada correctamente.')
            return redirect('obras')
    else:
        form = ObraForm()

    return render(request, 'obras/crear.html', {'form': form})


@login_required(login_url='login')
def obras_editar(request, obra_id):
    if request.user.role != 'INSPECTOR':
        return HttpResponseForbidden('No tienes permiso para editar obras.')

    obra = get_object_or_404(Obra, id=obra_id, inspector=request.user)

    if request.method == 'POST':
        form = ObraForm(request.POST, instance=obra)
        if form.is_valid():
            form.save()
            messages.success(request, 'Obra actualizada correctamente.')
            return redirect('obras_detalle', obra_id=obra.id)
    else:
        form = ObraForm(instance=obra)

    return render(request, 'obras/editar.html', {'form': form, 'obra': obra})


@login_required(login_url='login')
def obras_eliminar(request, obra_id):
    if request.user.role != 'INSPECTOR':
        return HttpResponseForbidden('No tienes permiso.')

    obra = get_object_or_404(Obra, id=obra_id, inspector=request.user)

    if request.method == 'POST':
        obra.delete()
        messages.success(request, 'Obra eliminada correctamente.')
        return redirect('obras')

    return redirect('obras_detalle', obra_id=obra.id)


# =========================
# CONTRATOS
# =========================

@login_required(login_url='login')
def contratos_lista(request):
    user = request.user

    if user.role == 'INSPECTOR':
        contratos = Contrato.objects.filter(obra__inspector=user)
    elif user.role == 'CONTRATISTA':
        contratos = Contrato.objects.filter(obra__empresa=user)
    else:
        contratos = Contrato.objects.none()

    return render(request, 'contratos/lista.html', {
        'contratos': contratos
    })


@login_required(login_url='login')
def contratos_detalle(request, contrato_id):
    user = request.user

    if user.role == 'INSPECTOR':
        contrato = get_object_or_404(
            Contrato,
            id=contrato_id,
            obra__inspector=user
        )
    else:
        contrato = get_object_or_404(
            Contrato,
            id=contrato_id,
            obra__empresa=user
        )

    garantias = Garantia.objects.filter(
        contrato=contrato
    ).order_by('fecha_termino_vigencia')

    return render(request, 'contratos/detalle.html', {
        'contrato': contrato,
        'garantias': garantias,
    })


@login_required(login_url='login')
def contratos_crear(request):
    if request.user.role != 'INSPECTOR':
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = ContratoForm(request.POST, inspector=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Contrato creado correctamente.')
            return redirect('contratos')
    else:
        form = ContratoForm(inspector=request.user)

    return render(request, 'contratos/crear.html', {'form': form})


@login_required(login_url='login')
def contratos_editar(request, contrato_id):
    if request.user.role != 'INSPECTOR':
        return HttpResponseForbidden()

    contrato = get_object_or_404(
        Contrato,
        id=contrato_id,
        obra__inspector=request.user
    )

    if request.method == 'POST':
        form = ContratoForm(
            request.POST,
            instance=contrato,
            inspector=request.user
        )
        if form.is_valid():
            form.save()
            messages.success(request, 'Contrato actualizado correctamente.')
            return redirect('contratos_detalle', contrato_id=contrato.id)
    else:
        form = ContratoForm(
            instance=contrato,
            inspector=request.user
        )

    return render(request, 'contratos/editar.html', {
        'form': form,
        'contrato': contrato
    })


@login_required(login_url='login')
def contratos_eliminar(request, contrato_id):
    if request.user.role != 'INSPECTOR':
        return HttpResponseForbidden()

    contrato = get_object_or_404(
        Contrato,
        id=contrato_id,
        obra__inspector=request.user
    )

    if request.method == 'POST':
        contrato.delete()
        messages.success(request, 'Contrato eliminado correctamente.')
        return redirect('contratos')

    return redirect('contratos_detalle', contrato_id=contrato.id)


# =========================
# GARANTÍAS
# =========================

@login_required(login_url='login')
def garantia_crear(request, contrato_id):
    if request.user.role != 'INSPECTOR':
        return HttpResponseForbidden()

    contrato = get_object_or_404(
        Contrato,
        id=contrato_id,
        obra__inspector=request.user
    )

    if request.method == 'POST':
        form = GarantiaForm(request.POST)
        if form.is_valid():
            garantia = form.save(commit=False)
            garantia.contrato = contrato
            garantia.save()
            messages.success(request, 'Garantía creada correctamente.')
            return redirect('contratos_detalle', contrato_id=contrato.id)
    else:
        form = GarantiaForm()

    return render(request, 'garantias/crear.html', {
        'form': form,
        'contrato': contrato
    })


@login_required(login_url='login')
def garantia_editar(request, garantia_id):
    if request.user.role != 'INSPECTOR':
        return HttpResponseForbidden()

    garantia = get_object_or_404(
        Garantia,
        id=garantia_id,
        contrato__obra__inspector=request.user
    )

    if request.method == 'POST':
        form = GarantiaForm(request.POST, instance=garantia)
        if form.is_valid():
            form.save()
            messages.success(request, 'Garantía actualizada correctamente.')
            return redirect('contratos_detalle', contrato_id=garantia.contrato.id)
    else:
        form = GarantiaForm(instance=garantia)

    return render(request, 'garantias/editar.html', {
        'form': form,
        'garantia': garantia
    })


@login_required(login_url='login')
def garantia_eliminar(request, garantia_id):
    if request.user.role != 'INSPECTOR':
        return HttpResponseForbidden()

    garantia = get_object_or_404(
        Garantia,
        id=garantia_id,
        contrato__obra__inspector=request.user
    )

    contrato_id = garantia.contrato.id

    if request.method == 'POST':
        garantia.delete()
        messages.success(request, 'Garantía eliminada correctamente.')
        return redirect('contratos_detalle', contrato_id=contrato_id)

    return redirect('contratos_detalle', contrato_id=contrato_id)


# =========================
# ESTADOS DE PAGO
# =========================

@login_required(login_url='login')
def edp_lista(request):
    user = request.user

    if user.role == 'INSPECTOR':
        edps = EstadoPago.objects.filter(obra__inspector=user)
    elif user.role == 'CONTRATISTA':
        edps = EstadoPago.objects.filter(obra__empresa=user)
    else:
        edps = EstadoPago.objects.none()

    busqueda = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', '').strip()

    if busqueda:
        edps = edps.filter(
            Q(obra__nombre__icontains=busqueda) |
            Q(obra__codigo__icontains=busqueda)
        )

    if estado:
        edps = edps.filter(estado=estado)

    filtros_activos = 0
    if busqueda:
        filtros_activos += 1
    if estado:
        filtros_activos += 1

    context = {
        'edps': edps,
        'busqueda': busqueda,
        'estado_actual': estado,
        'estado_choices': EstadoPago.ESTADO_CHOICES,
        'filtros_activos': filtros_activos,
    }

    return render(request, 'edp/lista.html', context)


@login_required(login_url='login')
def edp_detalle(request, edp_id):
    user = request.user

    if user.role == 'INSPECTOR':
        edp = get_object_or_404(
            EstadoPago,
            id=edp_id,
            obra__inspector=user
        )
    elif user.role == 'CONTRATISTA':
        edp = get_object_or_404(
            EstadoPago,
            id=edp_id,
            obra__empresa=user
        )
    else:
        edp = get_object_or_404(EstadoPago, id=edp_id)

    return render(request, 'edp/detalle.html', {
        'edp': edp
    })


def obtener_edp_anterior(edp):
    return EstadoPago.objects.filter(
        obra=edp.obra,
        numero_estado_pago__lt=edp.numero_estado_pago
    ).order_by('-numero_estado_pago').first()


def obtener_partida_anterior(partida):
    edp_anterior = obtener_edp_anterior(partida.estado_pago)

    if not edp_anterior:
        return None

    return PartidaEstadoPago.objects.filter(
        estado_pago=edp_anterior,
        item=partida.item
    ).first()


def recalcular_partida_acumulada(partida):
    if partida.tipo_fila == 'TITULO':
        partida.porcentaje_avance_periodo = 0
        partida.porcentaje_avance_acumulado = 0
        return partida

    partida_anterior = obtener_partida_anterior(partida)

    acumulado_anterior = 0

    if partida_anterior:
        acumulado_anterior = partida_anterior.porcentaje_avance_acumulado

    nuevo_acumulado = acumulado_anterior + partida.porcentaje_avance_periodo

    if nuevo_acumulado > 100:
        nuevo_acumulado = 100

    if nuevo_acumulado < 0:
        nuevo_acumulado = 0

    partida.porcentaje_avance_acumulado = nuevo_acumulado

    return partida


def clonar_partidas_desde_edp_anterior(edp_nuevo):
    edp_anterior = obtener_edp_anterior(edp_nuevo)

    if not edp_anterior:
        return

    if edp_nuevo.partidas.exists():
        return

    for partida in edp_anterior.partidas.all():
        PartidaEstadoPago.objects.create(
            estado_pago=edp_nuevo,
            tipo_fila=partida.tipo_fila,
            item=partida.item,
            nombre_partida=partida.nombre_partida,
            unidad=partida.unidad,
            cantidad=partida.cantidad,
            precio_unitario=partida.precio_unitario,
            porcentaje_avance_periodo=0,
            porcentaje_avance_acumulado=partida.porcentaje_avance_acumulado,
        )


@login_required(login_url='login')
def edp_crear(request):
    if request.user.role != 'INSPECTOR':
        return HttpResponseForbidden('No tienes permiso para crear estados de pago.')

    if request.method == 'POST':
        form = EstadoPagoForm(request.POST, inspector=request.user)

        if form.is_valid():
            edp = form.save(commit=False)

            edp.fecha_termino_periodo = edp.fecha_inicio_periodo

            edp_anterior = obtener_edp_anterior(edp)

            if edp_anterior:
                edp.tiene_anticipo = edp_anterior.tiene_anticipo
                edp.porcentaje_anticipo = edp_anterior.porcentaje_anticipo
                edp.porcentaje_gastos_generales = edp_anterior.porcentaje_gastos_generales
                edp.porcentaje_utilidades = edp_anterior.porcentaje_utilidades

            edp.save()

            clonar_partidas_desde_edp_anterior(edp)

            messages.success(
                request,
                f'El Estado de Pago N° {edp.numero_estado_pago} fue creado correctamente.'
            )

            return redirect('edp_detalle', edp_id=edp.id)
    else:
        form = EstadoPagoForm(inspector=request.user)

    return render(request, 'edp/crear.html', {
        'form': form
    })


@login_required(login_url='login')
def edp_editar(request, edp_id):
    if request.user.role != 'INSPECTOR':
        return HttpResponseForbidden('No tienes permiso para editar estados de pago.')

    edp = get_object_or_404(
        EstadoPago,
        id=edp_id,
        obra__inspector=request.user
    )

    if request.method == 'POST':
        form = EstadoPagoForm(request.POST, instance=edp, inspector=request.user)

        if form.is_valid():
            edp_editado = form.save(commit=False)

            edp_editado.fecha_termino_periodo = edp_editado.fecha_inicio_periodo

            edp_anterior = obtener_edp_anterior(edp_editado)

            if edp_anterior:
                edp_editado.tiene_anticipo = edp_anterior.tiene_anticipo
                edp_editado.porcentaje_anticipo = edp_anterior.porcentaje_anticipo

            edp_editado.save()

            messages.success(
                request,
                f'El Estado de Pago N° {edp_editado.numero_estado_pago} fue actualizado correctamente.'
            )

            return redirect('edp_detalle', edp_id=edp.id)
    else:
        form = EstadoPagoForm(instance=edp, inspector=request.user)

    return render(request, 'edp/editar.html', {
        'form': form,
        'edp': edp
    })


@login_required(login_url='login')
def edp_eliminar(request, edp_id):
    if request.user.role != 'INSPECTOR':
        return HttpResponseForbidden('No tienes permiso para eliminar estados de pago.')

    edp = get_object_or_404(
        EstadoPago,
        id=edp_id,
        obra__inspector=request.user
    )

    if request.method == 'POST':
        numero = edp.numero_estado_pago
        edp.delete()
        messages.success(request, f'El Estado de Pago N° {numero} fue eliminado correctamente.')
        return redirect('edp')

    return redirect('edp_detalle', edp_id=edp.id)


@login_required(login_url='login')
def partida_edp_crear(request, edp_id):
    if request.user.role != 'INSPECTOR':
        return HttpResponseForbidden('No tienes permiso para crear partidas.')

    edp = get_object_or_404(
        EstadoPago,
        id=edp_id,
        obra__inspector=request.user
    )

    if request.method == 'POST':
        form = PartidaEstadoPagoForm(request.POST, estado_pago=edp)

        if form.is_valid():
            partida = form.save(commit=False)
            partida.estado_pago = edp
            partida = recalcular_partida_acumulada(partida)
            partida.save()

            messages.success(request, 'Fila agregada correctamente.')
            return redirect('edp_detalle', edp_id=edp.id)
    else:
        form = PartidaEstadoPagoForm(estado_pago=edp)

    return render(request, 'edp/partida_crear.html', {
        'form': form,
        'edp': edp
    })


@login_required(login_url='login')
def partida_edp_editar(request, partida_id):
    if request.user.role != 'INSPECTOR':
        return HttpResponseForbidden('No tienes permiso para editar partidas.')

    partida = get_object_or_404(
        PartidaEstadoPago,
        id=partida_id,
        estado_pago__obra__inspector=request.user
    )

    if request.method == 'POST':
        form = PartidaEstadoPagoForm(
            request.POST,
            instance=partida,
            estado_pago=partida.estado_pago
        )

        if form.is_valid():
            partida_editada = form.save(commit=False)
            partida_editada = recalcular_partida_acumulada(partida_editada)
            partida_editada.save()

            messages.success(request, 'Fila actualizada correctamente.')
            return redirect('edp_detalle', edp_id=partida.estado_pago.id)
    else:
        form = PartidaEstadoPagoForm(
            instance=partida,
            estado_pago=partida.estado_pago
        )

    return render(request, 'edp/partida_editar.html', {
        'form': form,
        'partida': partida
    })


@login_required(login_url='login')
def partida_edp_eliminar(request, partida_id):
    if request.user.role != 'INSPECTOR':
        return HttpResponseForbidden('No tienes permiso para eliminar partidas.')

    partida = get_object_or_404(
        PartidaEstadoPago,
        id=partida_id,
        estado_pago__obra__inspector=request.user
    )

    edp_id = partida.estado_pago.id

    if request.method == 'POST':
        partida.delete()
        messages.success(request, 'Partida eliminada correctamente.')
        return redirect('edp_detalle', edp_id=edp_id)

    return redirect('edp_detalle', edp_id=edp_id)


# =========================
# ACTAS
# =========================

@login_required(login_url='login')
def actas_lista(request):
    user = request.user

    if user.role == 'INSPECTOR':
        actas = Acta.objects.filter(obra__inspector=user)
    elif user.role == 'CONTRATISTA':
        actas = Acta.objects.filter(obra__empresa=user)
    else:
        actas = Acta.objects.none()

    busqueda = request.GET.get('q', '').strip()
    tipo = request.GET.get('tipo', '').strip()
    estado = request.GET.get('estado', '').strip()

    if busqueda:
        actas = actas.filter(
            Q(nombre_obra__icontains=busqueda) |
            Q(codigo_licitacion__icontains=busqueda) |
            Q(nombre_empresa__icontains=busqueda)
        )

    if tipo:
        actas = actas.filter(tipo_acta=tipo)

    if estado:
        actas = actas.filter(estado=estado)

    filtros_activos = 0
    if busqueda:
        filtros_activos += 1
    if tipo:
        filtros_activos += 1
    if estado:
        filtros_activos += 1

    return render(request, 'actas/lista.html', {
        'actas': actas,
        'busqueda': busqueda,
        'tipo_actual': tipo,
        'estado_actual': estado,
        'tipo_choices': Acta.TIPO_ACTA_CHOICES,
        'estado_choices': Acta.ESTADO_CHOICES,
        'filtros_activos': filtros_activos,
    })


@login_required(login_url='login')
def actas_detalle(request, acta_id):
    user = request.user

    if user.role == 'INSPECTOR':
        acta = get_object_or_404(
            Acta,
            id=acta_id,
            obra__inspector=user
        )
    elif user.role == 'CONTRATISTA':
        acta = get_object_or_404(
            Acta,
            id=acta_id,
            obra__empresa=user
        )
    else:
        acta = get_object_or_404(Acta, id=acta_id)

    config_acta = ConfiguracionActa.objects.first()

    return render(request, 'actas/detalle.html', {
        'acta': acta,
        'config_acta': config_acta,
    })


@login_required(login_url='login')
def actas_crear(request):
    if request.user.role != 'INSPECTOR':
        return HttpResponseForbidden('No tienes permiso para crear actas.')

    if request.method == 'POST':
        form = ActaForm(request.POST, inspector=request.user)
        if form.is_valid():
            acta = form.save()
            messages.success(request, f'El Acta N° {acta.numero_acta} fue creada correctamente.')
            return redirect('actas')
    else:
        form = ActaForm(inspector=request.user)
        form.fields['fecha_acta'].initial = timezone.localdate()
        form.fields['estado'].initial = 'PENDIENTE'
        form.fields['nombre_inspector'].initial = request.user.username
        form.fields['firma_inspector_texto'].initial = request.user.username

    return render(request, 'actas/crear.html', {
        'form': form
    })


@login_required(login_url='login')
def actas_editar(request, acta_id):
    if request.user.role != 'INSPECTOR':
        return HttpResponseForbidden('No tienes permiso para editar actas.')

    acta = get_object_or_404(
        Acta,
        id=acta_id,
        obra__inspector=request.user
    )

    if request.method == 'POST':
        form = ActaForm(request.POST, instance=acta, inspector=request.user)
        if form.is_valid():
            acta_editada = form.save()
            messages.success(request, f'El Acta N° {acta_editada.numero_acta} fue actualizada correctamente.')
            return redirect('actas_detalle', acta_id=acta.id)
    else:
        form = ActaForm(instance=acta, inspector=request.user)

    return render(request, 'actas/editar.html', {
        'form': form,
        'acta': acta
    })


@login_required(login_url='login')
def actas_eliminar(request, acta_id):
    if request.user.role != 'INSPECTOR':
        return HttpResponseForbidden('No tienes permiso para eliminar actas.')

    acta = get_object_or_404(
        Acta,
        id=acta_id,
        obra__inspector=request.user
    )

    if request.method == 'POST':
        numero = acta.numero_acta
        acta.delete()
        messages.success(request, f'El Acta N° {numero} fue eliminada correctamente.')
        return redirect('actas')

    return redirect('actas_detalle', acta_id=acta.id)

@login_required(login_url='login')
def firmar_acta(request, acta_id):
    if request.method != 'POST':
        return redirect('actas')

    acta = get_object_or_404(Acta, id=acta_id)
    user = request.user

    # Firma Inspector
    if user.role == 'INSPECTOR':
        if acta.obra.inspector != user:
            return HttpResponseForbidden('No autorizado.')

        if not acta.firmado_inspector:
            acta.firmado_inspector = True
            acta.fecha_firma_inspector = timezone.now()
            acta.usuario_firma_inspector = user

            if not acta.firma_inspector_texto:
                acta.firma_inspector_texto = user.username

            acta.actualizar_estado_firma()
            acta.save()

            messages.success(request, 'Acta firmada por inspector correctamente.')
        else:
            messages.info(request, 'Esta acta ya fue firmada por el inspector.')

        return redirect('actas_detalle', acta_id=acta.id)

    # Firma Empresa
    if user.role == 'CONTRATISTA':
        if acta.obra.empresa != user:
            return HttpResponseForbidden('No autorizado.')

        if not acta.firmado_empresa:
            acta.firmado_empresa = True
            acta.fecha_firma_empresa = timezone.now()
            acta.usuario_firma_empresa = user

            if not acta.firma_empresa_texto:
                acta.firma_empresa_texto = user.username

            acta.actualizar_estado_firma()
            acta.save()

            messages.success(request, 'Acta firmada por empresa correctamente.')
        else:
            messages.info(request, 'Esta acta ya fue firmada por la empresa.')

        return redirect('documentos_detalle', documento_id=acta.id)

    return HttpResponseForbidden('No autorizado.')


@login_required(login_url='login')
def actas_pdf(request, acta_id):
    user = request.user

    if user.role == 'INSPECTOR':
        acta = get_object_or_404(Acta, id=acta_id, obra__inspector=user)
    elif user.role == 'CONTRATISTA':
        acta = get_object_or_404(Acta, id=acta_id, obra__empresa=user)
    else:
        return HttpResponseForbidden('No tienes permiso para ver esta acta.')

    config_acta = ConfiguracionActa.objects.first()

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="acta_{acta.numero_acta}.pdf"'

    pdf = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    x_margin = 50
    content_width = width - (x_margin * 2)
    y_top = height - 50
    y_bottom = 90

    def draw_footer(page_num):
        pdf.setFont("Helvetica", 8)
        pdf.setFillColor(colors.grey)
        pdf.drawString(x_margin, 30, "Generado desde OBRAFLOW")
        pdf.drawRightString(width - x_margin, 30, f"Página {page_num}")
        pdf.setFillColor(colors.black)

    def ensure_space(y, needed, page_num):
        if y - needed < y_bottom:
            draw_footer(page_num)
            pdf.showPage()
            page_num += 1
            return height - 60, page_num
        return y, page_num

    def draw_label_value(x, y, label, value):
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(x, y, f"{label}:")
        label_width = pdf.stringWidth(f"{label}: ", "Helvetica-Bold", 10)

        pdf.setFont("Helvetica", 10)
        pdf.drawString(x + label_width + 2, y, str(value or ""))

    def draw_justified_paragraph(text, x, y, max_width, font_name="Helvetica", font_size=10, line_height=16):
        pdf.setFont(font_name, font_size)

        paragraphs = text.splitlines()

        for paragraph in paragraphs:
            paragraph = paragraph.strip()

            if not paragraph:
                y -= line_height
                continue

            words = paragraph.split()
            lines = []
            current = []

            for word in words:
                test_line = " ".join(current + [word])

                if pdf.stringWidth(test_line, font_name, font_size) <= max_width:
                    current.append(word)
                else:
                    if current:
                        lines.append(current)
                    current = [word]

            if current:
                lines.append(current)

            for index, line_words in enumerate(lines):
                line_text = " ".join(line_words)

                if index == len(lines) - 1 or len(line_words) == 1:
                    pdf.drawString(x, y, line_text)
                else:
                    total_words_width = sum(
                        pdf.stringWidth(word, font_name, font_size)
                        for word in line_words
                    )
                    total_space = max_width - total_words_width
                    space_count = len(line_words) - 1
                    extra_space = total_space / space_count

                    current_x = x

                    for i, word in enumerate(line_words):
                        pdf.drawString(current_x, y, word)
                        current_x += pdf.stringWidth(word, font_name, font_size)

                        if i < space_count:
                            current_x += extra_space

                y -= line_height

        return y

    page_num = 1

    # =========================
    # ENCABEZADO FORMAL
    # =========================
    pdf.setFont("Helvetica-Bold", 10)

    if config_acta and config_acta.nombre_mandante:
        pdf.drawString(x_margin, y_top, config_acta.nombre_mandante)
    else:
        pdf.drawString(x_margin, y_top, "MANDANTE")

    pdf.setFont("Helvetica", 8)
    pdf.setFillColor(colors.grey)
    pdf.drawString(x_margin, y_top - 13, "Documento formal de obra")
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

    # =========================
    # TÍTULO PRINCIPAL
    # =========================
    y = y_top - 95

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawCentredString(width / 2, y, acta.titulo.upper())

    y -= 22
    pdf.setFont("Helvetica", 10)
    fecha_formateada = acta.fecha_acta.strftime("%d/%m/%Y")
    pdf.drawCentredString(width / 2, y, f"Acta N° {acta.numero_acta}  |  Fecha: {fecha_formateada}")

    y -= 40

    # =========================
    # ANTECEDENTES GENERALES
    # =========================
    y, page_num = ensure_space(y, 120, page_num)

    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(x_margin, y, "Antecedentes Generales")
    y -= 22

    y_left = y
    y_right = y

    draw_label_value(x_margin, y_left, "Obra", acta.nombre_obra)
    y_left -= 16

    draw_label_value(x_margin, y_left, "Código Licitación", acta.codigo_licitacion)
    y_left -= 16

    draw_label_value(x_margin, y_left, "Empresa", acta.nombre_empresa)
    y_left -= 16

    draw_label_value(x_margin, y_left, "RUT Empresa", acta.rut_empresa or "")
    y_left -= 16

    draw_label_value(width / 2 + 10, y_right, "Inspector a cargo", acta.nombre_inspector)
    y_right -= 16

    draw_label_value(width / 2 + 10, y_right, "Ubicación", acta.ubicacion_obra or "")
    y_right -= 16

    y = min(y_left, y_right) - 18

    pdf.setStrokeColor(colors.lightgrey)
    pdf.line(x_margin, y, width - x_margin, y)
    y -= 28

    # =========================
    # CONTENIDO
    # =========================
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(x_margin, y, "Contenido")
    y -= 24

    y = draw_justified_paragraph(
        acta.cuerpo_acta or "",
        x_margin,
        y,
        content_width,
        font_name="Helvetica",
        font_size=10,
        line_height=16
    )

    # =========================
    # OBSERVACIONES
    # =========================
    if acta.observaciones:
        y -= 24
        y, page_num = ensure_space(y, 50, page_num)

        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(x_margin, y, "Observaciones")
        y -= 22

        y = draw_justified_paragraph(
            acta.observaciones or "",
            x_margin,
            y,
            content_width,
            font_name="Helvetica",
            font_size=10,
            line_height=16
        )

    # =========================
    # FIRMAS CASI AL FINAL DE LA HOJA
    # =========================
    firma_y = 125

    if y < firma_y + 90:
        draw_footer(page_num)
        pdf.showPage()
        page_num += 1
        firma_y = 125

    left_x1 = x_margin + 20
    left_x2 = width / 2 - 30
    right_x1 = width / 2 + 30
    right_x2 = width - x_margin - 20

    inspector_nombre = acta.firma_inspector_texto or ""
    empresa_nombre = acta.firma_empresa_texto or ""

    pdf.setStrokeColor(colors.black)
    pdf.line(left_x1, firma_y, left_x2, firma_y)
    pdf.line(right_x1, firma_y, right_x2, firma_y)

    if acta.firmado_inspector:
        pdf.setFillColor(colors.blue)
        pdf.setFont("Helvetica-BoldOblique", 9)
        pdf.drawCentredString((left_x1 + left_x2) / 2, firma_y + 28, inspector_nombre)

        pdf.setFillColor(colors.green)
        pdf.setFont("Helvetica", 7)
        pdf.drawCentredString((left_x1 + left_x2) / 2, firma_y + 16, "Firmado digitalmente")

        if acta.fecha_firma_inspector:
            pdf.setFillColor(colors.grey)
            pdf.drawCentredString(
                (left_x1 + left_x2) / 2,
                firma_y + 6,
                acta.fecha_firma_inspector.strftime("%d/%m/%Y %H:%M")
            )
    else:
        pdf.setFillColor(colors.grey)
        pdf.setFont("Helvetica", 7)
        pdf.drawCentredString((left_x1 + left_x2) / 2, firma_y + 16, "Pendiente de firma")

    if acta.firmado_empresa:
        pdf.setFillColor(colors.blue)
        pdf.setFont("Helvetica-BoldOblique", 9)
        pdf.drawCentredString((right_x1 + right_x2) / 2, firma_y + 28, empresa_nombre)

        pdf.setFillColor(colors.green)
        pdf.setFont("Helvetica", 7)
        pdf.drawCentredString((right_x1 + right_x2) / 2, firma_y + 16, "Firmado digitalmente")

        if acta.fecha_firma_empresa:
            pdf.setFillColor(colors.grey)
            pdf.drawCentredString(
                (right_x1 + right_x2) / 2,
                firma_y + 6,
                acta.fecha_firma_empresa.strftime("%d/%m/%Y %H:%M")
            )
    else:
        pdf.setFillColor(colors.grey)
        pdf.setFont("Helvetica", 7)
        pdf.drawCentredString((right_x1 + right_x2) / 2, firma_y + 16, "Pendiente de firma")

    pdf.setFillColor(colors.black)

    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawCentredString((left_x1 + left_x2) / 2, firma_y - 15, inspector_nombre)
    pdf.drawCentredString((right_x1 + right_x2) / 2, firma_y - 15, empresa_nombre)

    pdf.setFont("Helvetica", 9)
    pdf.drawCentredString((left_x1 + left_x2) / 2, firma_y - 30, "Inspector Técnico de Obras")
    pdf.drawCentredString((right_x1 + right_x2) / 2, firma_y - 30, "Representante Empresa Contratista")

    draw_footer(page_num)

    pdf.save()
    return response

# =========================
# EDP PDF FIRMA
# =========================

@login_required(login_url='login')
def firmar_edp(request, edp_id):
    if request.method != 'POST':
        return redirect('edp')

    edp = get_object_or_404(EstadoPago, id=edp_id)
    user = request.user

    def nombre_usuario(usuario):
        nombre = f"{getattr(usuario, 'first_name', '')} {getattr(usuario, 'last_name', '')}".strip()
        return nombre if nombre else getattr(usuario, 'username', str(usuario))

    if user.role == 'INSPECTOR':
        if edp.obra.inspector != user:
            return HttpResponseForbidden('No autorizado.')

        if not edp.firmado_inspector:
            edp.firmado_inspector = True
            edp.fecha_firma_inspector = timezone.now()
            edp.usuario_firma_inspector = user
            edp.firma_inspector_texto = nombre_usuario(user)
            edp.actualizar_estado_firma()
            edp.save()

            messages.success(request, 'Estado de Pago firmado por inspector correctamente.')
        else:
            messages.info(request, 'Este Estado de Pago ya fue firmado por el inspector.')

        return redirect('edp_detalle', edp_id=edp.id)

    if user.role == 'CONTRATISTA':
        if edp.obra.empresa != user:
            return HttpResponseForbidden('No autorizado.')

        if not edp.firmado_inspector:
            messages.warning(request, 'La empresa no puede firmar hasta que el inspector firme primero.')
            return redirect('edp_detalle', edp_id=edp.id)

        if not edp.firmado_empresa:
            edp.firmado_empresa = True
            edp.fecha_firma_empresa = timezone.now()
            edp.usuario_firma_empresa = user
            edp.firma_empresa_texto = nombre_usuario(user)
            edp.actualizar_estado_firma()
            edp.save()

            messages.success(request, 'Estado de Pago firmado por empresa correctamente.')
        else:
            messages.info(request, 'Este Estado de Pago ya fue firmado por la empresa.')

        return redirect('edp_detalle', edp_id=edp.id)

    return HttpResponseForbidden('No autorizado.')

# =========================
# EDP PDF
# =========================

@login_required(login_url='login')
def edp_pdf(request, edp_id):
    user = request.user

    if user.role == 'INSPECTOR':
        edp = get_object_or_404(EstadoPago, id=edp_id, obra__inspector=user)
    elif user.role == 'CONTRATISTA':
        edp = get_object_or_404(EstadoPago, id=edp_id, obra__empresa=user)
    else:
        return HttpResponseForbidden('No tienes permiso para generar este PDF.')

    if user.role == 'CONTRATISTA' and edp.estado_firma != 'FIRMADA':
        messages.warning(
            request,
            'La empresa contratista solo puede generar el PDF cuando el Estado de Pago esté firmado por inspector y empresa.'
        )
        return redirect('edp_detalle', edp_id=edp.id)

    config_acta = ConfiguracionActa.objects.first()
    contrato = edp.obra.contratos.first()
    garantias = Garantia.objects.filter(contrato__obra=edp.obra)

    incluir_anterior = request.GET.get('comparativo') == '1' and edp.numero_estado_pago > 1

    edp_anterior = None
    if incluir_anterior:
        edp_anterior = EstadoPago.objects.filter(
            obra=edp.obra,
            numero_estado_pago__lt=edp.numero_estado_pago
        ).order_by('-numero_estado_pago').first()

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="edp_{edp.numero_estado_pago}_{edp.obra.codigo}.pdf"'

    pdf = canvas.Canvas(response, pagesize=A4)

    def clp(valor):
        try:
            return f"${int(valor):,}".replace(",", ".")
        except:
            return "$0"

    def porcentaje(valor):
        try:
            return f"{int(valor)}%"
        except:
            return "0%"

    def texto(valor):
        return str(valor) if valor not in [None, ""] else "-"

    def fecha(valor):
        try:
            return valor.strftime("%d/%m/%Y")
        except:
            return "-"

    def nombre_usuario(usuario):
        if not usuario:
            return "-"

        nombre = f"{getattr(usuario, 'first_name', '')} {getattr(usuario, 'last_name', '')}".strip()

        if nombre:
            return nombre

        return getattr(usuario, 'username', str(usuario))

    def texto_corto(valor, max_chars=38):
        valor = texto(valor)
        if len(valor) > max_chars:
            return valor[:max_chars - 3] + "..."
        return valor

    def campus_legible(valor):
        if not valor:
            return "-"

        return str(valor).replace("_", " ").title()

    def draw_wrapped_text(pdf, text, x, y, max_chars=38, line_height=10):
        text = texto(text)
        words = text.split()
        lines = []
        current = ""

        for word in words:
            test = f"{current} {word}".strip()

            if len(test) <= max_chars:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word

        if current:
            lines.append(current)

        for line in lines:
            pdf.drawString(x, y, line)
            y -= line_height

        return y

    def draw_header(pdf, width, height):
        x_margin = 50
        y_top = height - 35

        pdf.setFont("Helvetica-Bold", 10)

        if config_acta and config_acta.nombre_mandante:
            pdf.drawString(x_margin, y_top, config_acta.nombre_mandante)
        else:
            pdf.drawString(x_margin, y_top, "MANDANTE")

        pdf.setFont("Helvetica", 8)
        pdf.setFillColor(colors.grey)
        pdf.drawString(x_margin, y_top - 13, "Documento formal de obra")
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

    def draw_footer(pdf, page_num, width):
        pdf.setFont("Helvetica", 8)
        pdf.setFillColor(colors.grey)
        pdf.drawString(50, 30, "Generado desde OBRAFLOW")
        pdf.drawRightString(width - 50, 30, f"Página {page_num}")
        pdf.setFillColor(colors.black)

    def draw_section_title(pdf, x, y, title, width_line=720):
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(x, y, title)
        pdf.setStrokeColor(colors.lightgrey)
        pdf.line(x, y - 6, x + width_line, y - 6)
        pdf.setStrokeColor(colors.black)

    def draw_label_value(pdf, x, y, label, value, label_width=95, max_chars=34):
        pdf.setFont("Helvetica-Bold", 8.5)
        pdf.drawString(x, y, f"{label}:")
        pdf.setFont("Helvetica", 8.5)

        final_y = draw_wrapped_text(
            pdf,
            value,
            x + label_width,
            y,
            max_chars=max_chars,
            line_height=10
        )

        return final_y

    def draw_resumen_linea(pdf, x, y, width, label, value, destacado=False, total=False):
        if total:
            pdf.setFillColor(colors.Color(0.86, 0.94, 0.86))
            pdf.rect(x, y - 4, width, 16, fill=1, stroke=0)
        elif destacado:
            pdf.setFillColor(colors.Color(0.92, 0.92, 0.92))
            pdf.rect(x, y - 4, width, 16, fill=1, stroke=0)

        pdf.setFillColor(colors.black)
        pdf.setFont("Helvetica-Bold" if destacado or total else "Helvetica", 8.5)
        pdf.drawString(x + 6, y, label)
        pdf.drawRightString(x + width - 6, y, value)

    def obtener_partida_anterior_pdf(partida):
        if not edp_anterior:
            return None

        return PartidaEstadoPago.objects.filter(
            estado_pago=edp_anterior,
            item=partida.item,
            tipo_fila='PARTIDA'
        ).first()

    # =========================
    # HOJA 1 - VERTICAL
    # =========================
    width, height = A4
    draw_header(pdf, width, height)

    y = height - 95

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawCentredString(width / 2, y, f"ESTADO DE PAGO N° {edp.numero_estado_pago}")

    y -= 18
    pdf.setFont("Helvetica", 9)
    pdf.drawCentredString(width / 2, y, f"Fecha de emisión: {fecha(edp.fecha_inicio_periodo)}")

    y -= 14
    pdf.drawCentredString(width / 2, y, f"Obra: {texto_corto(edp.obra.nombre, 70)}")

    y -= 14
    pdf.drawCentredString(width / 2, y, f"Código licitación: {edp.obra.codigo}")

    y -= 34

    draw_section_title(pdf, 50, y, "1. Antecedentes de la obra", width_line=495)
    y -= 24

    if hasattr(edp.obra, 'get_campus_display'):
        campus = edp.obra.get_campus_display()
    else:
        campus = campus_legible(getattr(edp.obra, 'campus', None))

    ubicacion = (
        getattr(edp.obra, 'ubicacion', None)
        or getattr(edp.obra, 'direccion', None)
        or "-"
    )

    y_left = draw_label_value(pdf, 55, y, "Obra", edp.obra.nombre, max_chars=42)
    y_right = draw_label_value(pdf, 315, y, "Código", edp.obra.codigo, max_chars=28)
    y = min(y_left, y_right) - 6

    y_left = draw_label_value(pdf, 55, y, "Campus", campus, max_chars=42)
    y_right = draw_label_value(pdf, 315, y, "Ubicación", ubicacion, max_chars=30)
    y = min(y_left, y_right) - 6

    y_left = draw_label_value(pdf, 55, y, "Empresa", nombre_usuario(edp.obra.empresa), max_chars=42)
    y_right = draw_label_value(pdf, 315, y, "Inspector", nombre_usuario(edp.obra.inspector), max_chars=30)
    y = min(y_left, y_right)

    y -= 28

    draw_section_title(pdf, 50, y, "2. Antecedentes contractuales", width_line=495)
    y -= 24

    if contrato:
        y_left = draw_label_value(pdf, 55, y, "N° contrato", getattr(contrato, 'numero_contrato', '-'), max_chars=42)
        y_right = draw_label_value(
            pdf,
            315,
            y,
            "Tipo contrato",
            getattr(contrato, 'get_tipo_contrato_display', lambda: getattr(contrato, 'tipo_contrato', '-'))(),
            max_chars=30
        )
        y = min(y_left, y_right) - 6

        y_left = draw_label_value(pdf, 55, y, "Monto proyecto", clp(getattr(contrato, 'monto', 0)), max_chars=42)
        y_right = draw_label_value(pdf, 315, y, "Plazo", f"{getattr(contrato, 'plazo_dias', '-')} días", max_chars=30)
        y = min(y_left, y_right) - 6

        y_left = draw_label_value(pdf, 55, y, "Fecha inicio", fecha(getattr(contrato, 'fecha_inicio', None)), max_chars=42)
        y_right = draw_label_value(pdf, 315, y, "Fecha término", fecha(getattr(contrato, 'fecha_termino', None)), max_chars=30)
        y = min(y_left, y_right)
    else:
        pdf.setFont("Helvetica", 8.5)
        pdf.drawString(55, y, "No existen contratos asociados.")
        y -= 14

    y -= 28

    draw_section_title(pdf, 50, y, "3. Garantías asociadas", width_line=495)
    y -= 24

    if garantias.exists():
        pdf.setFillColor(colors.Color(0.92, 0.92, 0.92))
        pdf.rect(55, y - 4, 440, 16, fill=1, stroke=0)
        pdf.setFillColor(colors.black)

        pdf.setFont("Helvetica-Bold", 8)
        pdf.drawString(62, y, "Tipo garantía")
        pdf.drawString(360, y, "Fecha vencimiento")
        y -= 16

        pdf.setFont("Helvetica", 8)
        for garantia in garantias[:5]:
            tipo_garantia = getattr(
                garantia,
                'get_tipo_garantia_display',
                lambda: getattr(garantia, 'tipo_garantia', '-')
            )()

            vencimiento = fecha(getattr(garantia, 'fecha_termino_vigencia', None))

            pdf.drawString(62, y, texto_corto(tipo_garantia, 48))
            pdf.drawString(360, y, vencimiento)
            y -= 14
    else:
        pdf.setFont("Helvetica", 8.5)
        pdf.drawString(55, y, "No existen garantías asociadas.")
        y -= 14

    y -= 20

    draw_section_title(pdf, 50, y, "4. Resumen financiero principal", width_line=495)
    y -= 25

    resumen_x = 65
    resumen_w = 455

    resumen = [
        ("Subtotal partidas", clp(edp.subtotal_periodo), True, False),
        (f"Gastos generales ({porcentaje(edp.porcentaje_gastos_generales)})", clp(edp.gastos_generales), False, False),
        (f"Utilidades ({porcentaje(edp.porcentaje_utilidades)})", clp(edp.utilidades), False, False),
        ("Neto", clp(edp.neto), False, False),
        ("IVA (19%)", clp(edp.iva), False, False),
        ("Total general", clp(edp.total_general), True, False),
    ]

    if edp.tiene_anticipo:
        resumen.append(("Descuento anticipo", f"- {clp(edp.monto_descuento_anticipo)}", True, False))

    resumen.append(("Total a pagar EDP", clp(edp.total_a_pagar_edp), False, True))

    for label, value, destacado, total in resumen:
        draw_resumen_linea(pdf, resumen_x, y, resumen_w, label, value, destacado, total)
        y -= 17

    # =========================
    # FIRMAS EN PÁGINA 1
    # =========================
    firma_y = 78
    left_x1 = 85
    left_x2 = 280
    right_x1 = 315
    right_x2 = 510

    inspector_nombre = edp.firma_inspector_texto or nombre_usuario(edp.obra.inspector)
    empresa_nombre = edp.firma_empresa_texto or nombre_usuario(edp.obra.empresa)

    pdf.setStrokeColor(colors.black)
    pdf.line(left_x1, firma_y, left_x2, firma_y)
    pdf.line(right_x1, firma_y, right_x2, firma_y)

    if edp.firmado_inspector:
        pdf.setFillColor(colors.blue)
        pdf.setFont("Helvetica-BoldOblique", 9)
        pdf.drawCentredString((left_x1 + left_x2) / 2, firma_y + 28, inspector_nombre)

        pdf.setFillColor(colors.green)
        pdf.setFont("Helvetica", 7)
        pdf.drawCentredString((left_x1 + left_x2) / 2, firma_y + 16, "Firmado digitalmente")

        if edp.fecha_firma_inspector:
            pdf.setFillColor(colors.grey)
            pdf.drawCentredString(
                (left_x1 + left_x2) / 2,
                firma_y + 6,
                edp.fecha_firma_inspector.strftime("%d/%m/%Y %H:%M")
            )
    else:
        pdf.setFillColor(colors.grey)
        pdf.setFont("Helvetica", 7)
        pdf.drawCentredString((left_x1 + left_x2) / 2, firma_y + 16, "Pendiente de firma")

    if edp.firmado_empresa:
        pdf.setFillColor(colors.blue)
        pdf.setFont("Helvetica-BoldOblique", 9)
        pdf.drawCentredString((right_x1 + right_x2) / 2, firma_y + 28, empresa_nombre)

        pdf.setFillColor(colors.green)
        pdf.setFont("Helvetica", 7)
        pdf.drawCentredString((right_x1 + right_x2) / 2, firma_y + 16, "Firmado digitalmente")

        if edp.fecha_firma_empresa:
            pdf.setFillColor(colors.grey)
            pdf.drawCentredString(
                (right_x1 + right_x2) / 2,
                firma_y + 6,
                edp.fecha_firma_empresa.strftime("%d/%m/%Y %H:%M")
            )
    else:
        pdf.setFillColor(colors.grey)
        pdf.setFont("Helvetica", 7)
        pdf.drawCentredString((right_x1 + right_x2) / 2, firma_y + 16, "Pendiente de firma")

    pdf.setFillColor(colors.black)

    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawCentredString((left_x1 + left_x2) / 2, firma_y - 14, inspector_nombre)
    pdf.drawCentredString((right_x1 + right_x2) / 2, firma_y - 14, empresa_nombre)

    pdf.setFont("Helvetica", 7)
    pdf.drawCentredString((left_x1 + left_x2) / 2, firma_y - 27, "Inspector Técnico de Obras")
    pdf.drawCentredString((right_x1 + right_x2) / 2, firma_y - 27, "Representante Empresa Contratista")

    draw_footer(pdf, 1, width)

    pdf.showPage()

    # =========================
    # HOJA 2 - HORIZONTAL
    # =========================
    pdf.setPageSize(landscape(A4))
    width, height = landscape(A4)

    draw_header(pdf, width, height)

    y = height - 85

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawCentredString(width / 2, y, f"PLANILLA DE PARTIDAS - ESTADO DE PAGO N° {edp.numero_estado_pago}")

    y -= 25

    if incluir_anterior and edp_anterior:
        headers = [
            "Ítem", "Partida", "Unidad", "Cant.", "P.Unit.",
            "Monto Total", "% EDP Ant.", "Monto Ant.",
            "% EDP", "Monto EDP", "% Rest.", "Saldo"
        ]
        widths = [35, 110, 45, 45, 60, 70, 60, 70, 55, 70, 55, 75]
    else:
        headers = [
            "Ítem", "Partida", "Unidad", "Cant.", "P.Unit.",
            "Monto Total", "% EDP", "Monto EDP", "% Rest.", "Saldo"
        ]
        widths = [40, 160, 50, 50, 70, 90, 65, 90, 65, 95]

    x_start = 30
    row_h = 18

    pdf.setFont("Helvetica-Bold", 7)
    pdf.setFillColor(colors.Color(0.90, 0.90, 0.90))

    x = x_start
    for i, header in enumerate(headers):
        pdf.rect(x, y, widths[i], row_h, fill=1, stroke=1)
        pdf.setFillColor(colors.black)
        pdf.drawString(x + 3, y + 6, header)
        pdf.setFillColor(colors.Color(0.90, 0.90, 0.90))
        x += widths[i]

    pdf.setFillColor(colors.black)
    y -= row_h

    pdf.setFont("Helvetica", 7)

    for partida in edp.partidas.all():
        if y < 120:
            draw_footer(pdf, 2, width)
            pdf.showPage()
            pdf.setPageSize(landscape(A4))
            width, height = landscape(A4)
            draw_header(pdf, width, height)
            y = height - 85

        if partida.tipo_fila == 'TITULO':
            total_width = sum(widths)

            pdf.setFillColor(colors.Color(0.86, 0.86, 0.86))
            pdf.rect(x_start, y, total_width, row_h, fill=1, stroke=1)
            pdf.setFillColor(colors.black)

            pdf.setFont("Helvetica-Bold", 7)
            pdf.drawString(x_start + 4, y + 6, f"{partida.item}  {partida.nombre_partida.upper()}")
            pdf.setFont("Helvetica", 7)

            y -= row_h
            continue

        partida_anterior = obtener_partida_anterior_pdf(partida)

        if partida_anterior:
            porcentaje_anterior = porcentaje(partida_anterior.porcentaje_avance_periodo)
            monto_anterior = clp(partida_anterior.monto_periodo)
        else:
            porcentaje_anterior = "0%"
            monto_anterior = "$0"

        if incluir_anterior and edp_anterior:
            values = [
                partida.item,
                texto_corto(partida.nombre_partida, 24),
                texto(partida.unidad),
                str(int(partida.cantidad)),
                clp(partida.precio_unitario),
                clp(partida.monto_total_partida),
                porcentaje_anterior,
                monto_anterior,
                porcentaje(partida.porcentaje_avance_periodo),
                clp(partida.monto_periodo),
                porcentaje(partida.porcentaje_restante),
                clp(partida.saldo_restante),
            ]
        else:
            values = [
                partida.item,
                texto_corto(partida.nombre_partida, 34),
                texto(partida.unidad),
                str(int(partida.cantidad)),
                clp(partida.precio_unitario),
                clp(partida.monto_total_partida),
                porcentaje(partida.porcentaje_avance_periodo),
                clp(partida.monto_periodo),
                porcentaje(partida.porcentaje_restante),
                clp(partida.saldo_restante),
            ]

        x = x_start
        for i, value in enumerate(values):
            pdf.rect(x, y, widths[i], row_h, fill=0, stroke=1)
            pdf.drawString(x + 3, y + 6, str(value))
            x += widths[i]

        y -= row_h

    resumen_w = 430
    resumen_h = 138
    resumen_x = width - resumen_w - 40
    resumen_y = 58

    pdf.setFillColor(colors.Color(0.96, 0.96, 0.96))
    pdf.rect(resumen_x, resumen_y, resumen_w, resumen_h, fill=1, stroke=1)
    pdf.setFillColor(colors.black)

    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawString(resumen_x + 10, resumen_y + resumen_h - 16, "Resumen General")

    resumen_lineas = [
        ("Subtotal Partidas", clp(edp.subtotal_periodo), True, False),
        (f"Gastos Generales ({porcentaje(edp.porcentaje_gastos_generales)})", clp(edp.gastos_generales), False, False),
        (f"Utilidades ({porcentaje(edp.porcentaje_utilidades)})", clp(edp.utilidades), False, False),
        ("Neto", clp(edp.neto), False, False),
        ("IVA (19%)", clp(edp.iva), False, False),
        ("Total General", clp(edp.total_general), True, False),
    ]

    if edp.tiene_anticipo:
        resumen_lineas.append(("Descuento Anticipo", f"- {clp(edp.monto_descuento_anticipo)}", True, False))

    resumen_lineas.append(("Total a Pagar EDP", clp(edp.total_a_pagar_edp), False, True))

    y_res = resumen_y + resumen_h - 30

    for label, value, destacado, total in resumen_lineas:
        if total:
            pdf.setFillColor(colors.Color(0.86, 0.94, 0.86))
            pdf.rect(resumen_x + 6, y_res - 4, resumen_w - 12, 12, fill=1, stroke=0)
        elif destacado:
            pdf.setFillColor(colors.Color(0.91, 0.91, 0.91))
            pdf.rect(resumen_x + 6, y_res - 4, resumen_w - 12, 12, fill=1, stroke=0)

        pdf.setFillColor(colors.black)
        pdf.setFont("Helvetica-Bold" if destacado or total else "Helvetica", 6.8)
        pdf.drawString(resumen_x + 12, y_res, label)
        pdf.drawRightString(resumen_x + resumen_w - 12, y_res, value)
        y_res -= 12

    draw_footer(pdf, 2, width)

    pdf.save()
    return response

# =========================
# TRABAJADORES
# =========================

@login_required(login_url='login')
def trabajadores_lista(request):
    user = request.user

    if user.role == 'CONTRATISTA':
        trabajadores = Trabajador.objects.filter(obra__empresa=user)
    elif user.role == 'INSPECTOR':
        trabajadores = Trabajador.objects.filter(obra__inspector=user)
    else:
        trabajadores = Trabajador.objects.none()

    busqueda = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', '').strip()

    if busqueda:
        trabajadores = trabajadores.filter(
            Q(nombres__icontains=busqueda) |
            Q(apellidos__icontains=busqueda) |
            Q(rut__icontains=busqueda) |
            Q(obra__nombre__icontains=busqueda) |
            Q(obra__codigo__icontains=busqueda)
        )

    if estado:
        trabajadores = trabajadores.filter(estado=estado)

    filtros_activos = 0
    if busqueda:
        filtros_activos += 1
    if estado:
        filtros_activos += 1

    return render(request, 'trabajadores/lista.html', {
        'trabajadores': trabajadores,
        'busqueda': busqueda,
        'estado_actual': estado,
        'estado_choices': Trabajador.ESTADO_CHOICES,
        'filtros_activos': filtros_activos,
    })


@login_required(login_url='login')
def trabajadores_detalle(request, trabajador_id):
    user = request.user

    if user.role == 'CONTRATISTA':
        trabajador = get_object_or_404(
            Trabajador,
            id=trabajador_id,
            obra__empresa=user
        )
    elif user.role == 'INSPECTOR':
        trabajador = get_object_or_404(
            Trabajador,
            id=trabajador_id,
            obra__inspector=user
        )
    else:
        return HttpResponseForbidden('No tienes permiso para ver este trabajador.')

    return render(request, 'trabajadores/detalle.html', {
        'trabajador': trabajador
    })


@login_required(login_url='login')
def trabajadores_crear(request):
    if request.user.role != 'CONTRATISTA':
        return HttpResponseForbidden('No tienes permiso para crear trabajadores.')

    if request.method == 'POST':
        form = TrabajadorForm(request.POST, empresa=request.user)
        if form.is_valid():
            trabajador = form.save()
            messages.success(request, f'El trabajador {trabajador.nombres} {trabajador.apellidos} fue registrado correctamente.')
            return redirect('trabajadores')
    else:
        form = TrabajadorForm(empresa=request.user)

    return render(request, 'trabajadores/crear.html', {
        'form': form
    })


@login_required(login_url='login')
def trabajadores_editar(request, trabajador_id):
    if request.user.role != 'CONTRATISTA':
        return HttpResponseForbidden('No tienes permiso para editar trabajadores.')

    trabajador = get_object_or_404(
        Trabajador,
        id=trabajador_id,
        obra__empresa=request.user
    )

    if request.method == 'POST':
        form = TrabajadorForm(request.POST, instance=trabajador, empresa=request.user)
        if form.is_valid():
            trabajador_editado = form.save()
            messages.success(request, f'El trabajador {trabajador_editado.nombres} {trabajador_editado.apellidos} fue actualizado correctamente.')
            return redirect('trabajadores_detalle', trabajador_id=trabajador.id)
    else:
        form = TrabajadorForm(instance=trabajador, empresa=request.user)

    return render(request, 'trabajadores/editar.html', {
        'form': form,
        'trabajador': trabajador
    })


@login_required(login_url='login')
def trabajadores_eliminar(request, trabajador_id):
    if request.user.role != 'CONTRATISTA':
        return HttpResponseForbidden('No tienes permiso para eliminar trabajadores.')

    trabajador = get_object_or_404(
        Trabajador,
        id=trabajador_id,
        obra__empresa=request.user
    )

    if request.method == 'POST':
        nombre_completo = f'{trabajador.nombres} {trabajador.apellidos}'
        trabajador.delete()
        messages.success(request, f'El trabajador {nombre_completo} fue eliminado correctamente.')
        return redirect('trabajadores')

    return redirect('trabajadores_detalle', trabajador_id=trabajador.id)


@login_required(login_url='login')
def trabajador_documentos_editar(request, trabajador_id):
    if request.user.role != 'CONTRATISTA':
        return HttpResponseForbidden('No tienes permiso para subir documentos.')

    trabajador = get_object_or_404(
        Trabajador,
        id=trabajador_id,
        obra__empresa=request.user
    )

    documentos, created = DocumentoTrabajador.objects.get_or_create(
        trabajador=trabajador
    )

    if request.method == 'POST':
        form = DocumentoTrabajadorForm(
            request.POST,
            request.FILES,
            instance=documentos
        )

        if form.is_valid():
            form.save()
            messages.success(request, 'Documentos del trabajador actualizados correctamente.')
            return redirect('trabajadores_detalle', trabajador_id=trabajador.id)
    else:
        form = DocumentoTrabajadorForm(instance=documentos)

    return render(request, 'trabajadores/documentos_editar.html', {
        'form': form,
        'trabajador': trabajador,
        'documentos': documentos,
    })

# =========================
# DOCUMENTOS
# =========================


@login_required(login_url='login')
def documentos_lista(request):
    user = request.user

    if user.role == 'CONTRATISTA':
        documentos = Acta.objects.filter(
            obra__empresa=user
        ).order_by('-fecha_acta', '-id')
    elif user.role == 'INSPECTOR':
        documentos = Acta.objects.filter(
            obra__inspector=user
        ).order_by('-fecha_acta', '-id')
    else:
        documentos = Acta.objects.none()

    busqueda = request.GET.get('q', '').strip()
    tipo = request.GET.get('tipo', '').strip()
    estado = request.GET.get('estado', '').strip()

    if busqueda:
        documentos = documentos.filter(
            Q(nombre_obra__icontains=busqueda) |
            Q(codigo_licitacion__icontains=busqueda) |
            Q(nombre_empresa__icontains=busqueda)
        )

    if tipo:
        documentos = documentos.filter(tipo_acta=tipo)

    if estado:
        documentos = documentos.filter(estado=estado)

    filtros_activos = 0
    if busqueda:
        filtros_activos += 1
    if tipo:
        filtros_activos += 1
    if estado:
        filtros_activos += 1

    return render(request, 'documentos/lista.html', {
        'documentos': documentos,
        'busqueda': busqueda,
        'tipo_actual': tipo,
        'estado_actual': estado,
        'tipo_choices': Acta.TIPO_ACTA_CHOICES,
        'estado_choices': Acta.ESTADO_CHOICES,
        'filtros_activos': filtros_activos,
    })


@login_required(login_url='login')
def documentos_detalle(request, documento_id):
    user = request.user

    if user.role == 'CONTRATISTA':
        documento = get_object_or_404(
            Acta,
            id=documento_id,
            obra__empresa=user
        )
    elif user.role == 'INSPECTOR':
        documento = get_object_or_404(
            Acta,
            id=documento_id,
            obra__inspector=user
        )
    else:
        return HttpResponseForbidden('No tienes permiso para ver este documento.')

    config_acta = ConfiguracionActa.objects.first()

    return render(request, 'documentos/detalle.html', {
        'documento': documento,
        'config_acta': config_acta,
    })


@login_required(login_url='login')
def documentos_subir(request):
    return HttpResponseForbidden('Este módulo no permite subir documentos por ahora.')


# =========================
# OTROS
# =========================

@login_required(login_url='login')
def reportes_index(request):
    return render(request, 'reportes/index.html')


# =========================
# PERFIL DE USUARIO
# =========================

@login_required(login_url='login')
def perfil_usuario(request):
    if request.method == 'POST':
        form = PerfilUsuarioForm(request.POST, instance=request.user)

        if form.is_valid():
            form.save()
            messages.success(request, 'Tus datos fueron actualizados correctamente.')
            return redirect('perfil_usuario')
    else:
        form = PerfilUsuarioForm(instance=request.user)

    return render(request, 'usuarios/perfil.html', {
        'form': form
    })


@login_required(login_url='login')
def cambiar_password(request):
    if request.method == 'POST':
        form = CambiarPasswordForm(request.user, request.POST)

        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Tu contraseña fue actualizada correctamente.')
            return redirect('perfil_usuario')
    else:
        form = CambiarPasswordForm(request.user)

    return render(request, 'usuarios/cambiar_password.html', {
        'form': form
    })
