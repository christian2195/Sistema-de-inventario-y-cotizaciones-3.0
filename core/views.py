import io
import uuid
import qrcode
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum, Count, F, FloatField
from django.db.models.functions import Coalesce
from django.forms import inlineformset_factory
from django.template.loader import get_template
import csv
# Librerías de renderizado gráfico de reportes institucionales
from xhtml2pdf import pisa
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# Modelos maestros y transaccionales del núcleo de EMVEPRO
from .models import (
    Producto, Proveedor, Cliente, Cotizacion, 
    ItemCotizacion, ActaRecepcion, NotaDespacho, 
    ItemDespacho, PagoProveedor, Almacen
)

# Catálogo relacional de formularios de entrada de datos (¡AQUÍ IMPORTAMOS ITEMDESPACHOFORM!)
from .forms import (
    ProductoForm, CotizacionForm, ItemCotizacionFormSet, 
    ActaRecepcionForm, MovimientoRecepcionFormSet, 
    NotaDespachoForm, ItemDespachoForm, ItemDespachoFormSet
)

# ==============================================================================
# PROYECTO: EMVEPRO C.A.
# GERENCIA DE TECNOLOGÍA DE LA INFORMACIÓN Y COMUNICACIÓN
# ==============================================================================

@login_required
def dashboard_principal(request):
    """
    Vista del Dashboard Corporativo de EMVEPRO.
    Optimizado para calcular estadísticas en base a la arquitectura multidivisa (USD/Bs.)
    adaptada para los formatos reales de Fondo Negro Primero.
    """
    # 1. Métricas de Inventario Global (Corregido contra stock_minimo base)
    total_productos = Producto.objects.filter(activo=True).count()
    productos_bajo_stock = Producto.objects.filter(activo=True, stock_actual__lte=0.00).count()

    # 2. Métricas de Documentos y Flujo de Almacén
    total_cotizaciones = Cotizacion.objects.count()
    total_actas_recepcion = ActaRecepcion.objects.count()
    total_notas_despacho = NotaDespacho.objects.count()

    # 3. ESTADÍSTICAS FINANCIERAS CORREGIDAS (Opción B - Agregación Atómica)
    totales_items = ItemCotizacion.objects.aggregate(
        total_proyectado_usd=Sum(F('cantidad_solicitada') * F('pvp_unitario_usd'))
    )
    monto_proyectado_usd = totales_items['total_proyectado_usd'] or 0.00

    # 4. Estadísticas de Cotizaciones por Estatus y Totales Consolidados en Bolívares
    cotizaciones_pendientes = Cotizacion.objects.filter(estatus='PENDIENTE').count()
    cotizaciones_dotadas = Cotizacion.objects.filter(estatus='DOTADO').count()
    
    # Sumatoria total de los montos generales en Bolívares (BCV) y Dólares guardados en cabecera
    financiero_global = Cotizacion.objects.exclude(estatus='ANULADO').aggregate(
        acumulado_bs=Sum('total_bs'),
        acumulado_usd=Sum('total_usd')
    )
    total_general_bs = financiero_global['acumulado_bs'] or 0.00
    total_general_usd = financiero_global['acumulado_usd'] or 0.00

    # 5. Últimos movimientos para la tabla de actividad reciente (Auditoría)
    cotizaciones_recientes = Cotizacion.objects.select_related('cliente').order_by('-fecha_emision')[:5]
    despachos_recientes = NotaDespacho.objects.select_related('cotizacion', 'responsable').order_by('-fecha_despacho')[:5]

    context = {
        'total_productos': total_productos,
        'productos_bajo_stock': productos_bajo_stock,
        'total_cotizaciones': total_cotizaciones,
        'total_actas_recepcion': total_actas_recepcion,
        'total_notas_despacho': total_notas_despacho,
        'cotizaciones_pendientes': cotizaciones_pendientes,
        'cotizaciones_dotadas': cotizaciones_dotadas,
        'monto_proyectado_usd': monto_proyectado_usd,
        'total_general_bs': total_general_bs,
        'total_general_usd': total_general_usd,
        'cotizaciones_recientes': cotizaciones_recientes,
        'despachos_recientes': despachos_recientes,
    }
    return render(request, 'core/dashboard.html', context)


@login_required
def estatus_proyectos(request):
    """Pilar 4: Interfaz de Estatus de Proyectos"""
    cotizaciones = Cotizacion.objects.exclude(estatus='ANULADO').prefetch_related('items__despachos')
    proyectos_data = []
    
    for cot in cotizaciones:
        total_solicitado = 0
        total_despachado = 0
        
        for item in cot.items.all():
            total_solicitado += item.cantidad_solicitada
            despachado_item = sum(despacho.cantidad_despachada for despacho in item.despachos.all())
            total_despachado += despachado_item
            
        porcentaje = (total_despachado / total_solicitado) * 100 if total_solicitado > 0 else 0
            
        proyectos_data.append({
            'id': cot.id,
            'numero_rastreo': cot.numero_rastreo,
            'cliente': cot.cliente.nombre,
            'estatus': cot.get_estatus_display(),
            'porcentaje_dotacion': round(porcentaje, 2),
        })
        
    return render(request, 'core/estatus_proyectos.html', {'proyectos': proyectos_data})


@login_required
def finanzas_proveedores(request):
    """Pilar 5: Detalle de cuentas por pagar a proveedores"""
    proveedores = Proveedor.objects.all()
    datos_financieros = []

    for prov in proveedores:
        facturado = prov.actas_recepcion.aggregate(total=Coalesce(Sum('monto_total_factura', output_field=FloatField()), 0.0))['total']
        pagado = prov.pagos.aggregate(total=Coalesce(Sum('monto_pagado', output_field=FloatField()), 0.0))['total']
        deuda = facturado - pagado

        if facturado > 0 or pagado > 0:
            datos_financieros.append({
                'proveedor': prov.nombre,
                'total_facturado': round(facturado, 2),
                'total_pagado': round(pagado, 2),
                'deuda_actual': round(deuda, 2),
            })

    return render(request, 'core/finanzas_proveedores.html', {'datos_financieros': datos_financieros})


@login_required
def lista_productos(request):
    productos = Producto.objects.select_related('almacen').all().order_by('nombre')
    return render(request, 'core/producto_list.html', {'productos': productos})


@login_required
def crear_producto(request):
    """Renderiza y procesa el formulario para crear un nuevo producto"""
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('core:lista_productos')
    else:
        form = ProductoForm()
    
    return render(request, 'core/producto_form.html', {'form': form})


@login_required
def crear_cotizacion(request):
    """Genera una cotización institucional y todos sus ítems bajo la matemática multidivisa"""
    if request.method == 'POST':
        form = CotizacionForm(request.POST)
        formset = ItemCotizacionFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                cotizacion = form.save()
                formset.instance = cotizacion
                formset.save()
            return redirect('core:estatus_proyectos')
    else:
        form = CotizacionForm()
        formset = ItemCotizacionFormSet()

    context = {
        'form': form,
        'formset': formset,
    }
    return render(request, 'core/cotizacion_form.html', context)


@login_required
def crear_acta_recepcion(request):
    """Genera un Acta de Recepción, guarda los movimientos y suma el stock"""
    if request.method == 'POST':
        form = ActaRecepcionForm(request.POST)
        formset = MovimientoRecepcionFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                acta = form.save()
                movimientos = formset.save(commit=False)
                
                for mov in movimientos:
                    mov.acta_recepcion = acta
                    mov.almacen = acta.almacen
                    mov.responsable = acta.responsable
                    mov.tipo = 'ENTRADA'
                    mov.save()
                    
                    mov.producto.stock_actual += mov.cantidad
                    mov.producto.save()
                    
            return redirect('core:dashboard')
    else:
        form = ActaRecepcionForm()
        formset = MovimientoRecepcionFormSet()

    context = {
        'form': form,
        'formset': formset,
    }
    return render(request, 'core/recepcion_form.html', context)


@login_required
def crear_nota_despacho(request):
    """
    Vista operativa para generar Notas de Despacho y extraer ítems
    del inventario en Almacén Fuerte Tiuna aplicando widgets avanzados.
    """
    # Vinculamos la fábrica usando explícitamente tu formulario personalizado importado de forms.py
    ItemDespachoFormSetFactory = inlineformset_factory(
        NotaDespacho, 
        ItemDespacho,
        form=ItemDespachoForm,  # ¡SANEADO! Ahora sí se reconoce correctamente
        fields=['item_cotizacion', 'almacen_origen', 'cantidad_despachada', 'marca', 'modelo'],
        extra=1,
        can_delete=True
    )

    if request.method == 'POST':
        form = NotaDespachoForm(request.POST)
        formset = ItemDespachoFormSetFactory(request.POST)
        
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                nota_despacho = form.save(commit=False)
                nota_despacho.responsable = request.user
                nota_despacho.save()
                
                formset.instance = nota_despacho
                formset.save()
                
            return redirect('core:dashboard')
    else:
        form = NotaDespachoForm()
        formset = ItemDespachoFormSetFactory()

    context = {
        'form': form,
        'formset': formset,
    }
    return render(request, 'core/despacho_form.html', context)


@login_required
def generar_pdf_cotizacion(request, cotizacion_id):
    """Genera un documento PDF formal para la cotización seleccionada"""
    cotizacion = get_object_or_404(Cotizacion, id=cotizacion_id)
    context = {'cotizacion': cotizacion}
    template = get_template('core/cotizacion_pdf.html')
    html = template.render(context)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Cotizacion_EMVEPRO_{cotizacion.numero_rastreo}.pdf"'
    
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Tuvimos errores generando el PDF', status=500)
    
    return response


@login_required
def generar_pdf_despacho(request, despacho_id):
    """
    Genera el formato físico oficial en PDF de la Nota de Despacho del Almacén 
    Fuerte Tiuna con validación QR dinámica (Alineado con el PDF Ministerial original).
    """
    despacho = get_object_or_404(NotaDespacho, id=despacho_id)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Nota_Despacho_{despacho.numero_guia}.pdf"'
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    
    styles = getSampleStyleSheet()
    normal_style = ParagraphStyle('DocNormal', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=12)
    bold_style = ParagraphStyle('DocBold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, leading=12)
    header_table_style = ParagraphStyle('TableHeader', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, textColor=colors.white, alignment=1)

    url_validacion = request.build_absolute_uri(f"/core/dashboard/")
    
    qr = qrcode.QRCode(version=1, box_size=3, border=1)
    qr.add_data(url_validacion)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white")
    
    qr_buffer = io.BytesIO()
    img_qr.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    reportlab_qr = Image(qr_buffer, width=65, height=65)

    texto_institucion = """<b>Gobierno Bolivariano de Venezuela</b><br/>
    Ministerio del Poder Popular de Industrias y Producción Nacional<br/>
    Viceministerio de Industrias Intermedias y Ligeras<br/>
    <b>EMVEPRO C.A. / ALMACÉN FUERTE TIUNA</b>
    """
    
    info_guia = f"<b>NOTA DE DESPACHO</b><br/><font color='red'><b>Nro. {despacho.numero_guia}</b></font><br/>Fecha: {despacho.fecha_despacho.strftime('%d/%m/%Y %H:%M')}"
    
    data_top = [
        [Paragraph(texto_institucion, normal_style), reportlab_qr, Paragraph(info_guia, normal_style)]
    ]
    table_top = Table(data_top, colWidths=[260, 80, 210])
    table_top.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (2,0), (2,0), 'RIGHT'),
    ]))
    story.append(table_top)
    story.append(Spacer(1, 15))

    data_beneficiario = [
        [Paragraph("<b>NOMBRE DEL BENEFICIARIO:</b>", bold_style), Paragraph(despacho.nombre_beneficiario or "N/P", normal_style)],
        [Paragraph("<b>PROVEEDOR:</b>", bold_style), Paragraph(despacho.proveedor_origen or "EMVEPRO C.A.", normal_style)],
        [Paragraph("<b>N° ORDEN ASOCIADA / PROYECTO:</b>", bold_style), Paragraph(despacho.nro_orden_asociada or "N/P", normal_style)],
        [Paragraph("<b>NOTA DE ENTREGA ASOCIADA:</b>", bold_style), Paragraph(despacho.cotizacion.numero_rastreo, normal_style)]
    ]
    table_ben = Table(data_beneficiario, colWidths=[180, 370])
    table_ben.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D1D5DB')),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#F3F4F6')),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(table_ben)
    story.append(Spacer(1, 15))

    tabla_items_data = [[
        Paragraph("Items", header_table_style),
        Paragraph("Código / SKU", header_table_style),
        Paragraph("Producto / Descripción", header_table_style),
        Paragraph("Marca", header_table_style),
        Paragraph("Modelo", header_table_style),
        Paragraph("Cantidad", header_table_style)
    ]]
    
    total_cantidades = 0
    for idx, item in enumerate(despacho.items.all(), start=1):
        tabla_items_data.append([
            Paragraph(str(idx), normal_style),
            Paragraph(item.item_cotizacion.producto.codigo_sku, normal_style),
            Paragraph(item.item_cotizacion.producto.nombre, normal_style),
            Paragraph(item.marca or "-", normal_style),
            Paragraph(item.modelo or "-", normal_style),
            Paragraph(f"{item.cantidad_despachada:,.2f}", normal_style)
        ])
        total_cantidades += item.cantidad_despachada

    tabla_items_data.append([
        Paragraph("<b>TOTAL DE PRODUCTOS:</b>", bold_style), "", "", "", "",
        Paragraph(f"<b>{total_cantidades:,.2f}</b>", bold_style)
    ])

    table_items = Table(tabla_items_data, colWidths=[40, 90, 190, 75, 75, 80])
    table_items.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A252C')),
        ('GRID', (0,0), (-1,-2), 0.5, colors.HexColor('#9CA3AF')),
        ('ALIGN', (5,1), (5,-1), 'RIGHT'),
        ('SPAN', (0,-1), (4,-1)),
        ('PADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(table_items)
    story.append(Spacer(1, 15))

    data_transporte = [
        [Paragraph("<b>NOMBRE DEL CONDUCTOR:</b>", bold_style), Paragraph(despacho.nombre_conductor or "-", normal_style), Paragraph("<b>C.I. CONDUCTOR:</b>", bold_style), Paragraph(despacho.cedula_conductor or "-", normal_style)],
        [Paragraph("<b>TIPO DE VEHÍCULO:</b>", bold_style), Paragraph(despacho.tipo_vehiculo or "-", normal_style), Paragraph("<b>PLACA / COLOR:</b>", bold_style), Paragraph(f"{despacho.placa_vehiculo or '-'} / {despacho.color_vehiculo or '-'}", normal_style)],
        [Paragraph("<b>BENEFICIARIO AUTORIZADO:</b>", bold_style), Paragraph(despacho.beneficiario_autorizado or "-", normal_style), Paragraph("<b>C.I. / TELF:</b>", bold_style), Paragraph(f"{despacho.cedula_beneficiario or '-'} / {despacho.telefono_beneficiario or '-'}", normal_style)],
        [Paragraph("<b>LLEGADA CONDUCTOR:</b>", bold_style), Paragraph(despacho.fecha_hora_llegada_conductor.strftime('%d/%m/%Y %H:%M') if despacho.fecha_hora_llegada_conductor else "-", normal_style),
         Paragraph("<b>LLEGADA BENEFICIARIO:</b>", bold_style), Paragraph(despacho.fecha_hora_llegada_beneficiario.strftime('%d/%m/%Y %H:%M') if despacho.fecha_hora_llegada_beneficiario else "-", normal_style)]
    ]
    table_trans = Table(data_transporte, colWidths=[130, 145, 130, 145])
    table_trans.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D1D5DB')),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#F9FAFB')),
        ('BACKGROUND', (2,0), (2,-1), colors.HexColor('#F9FAFB')),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(table_trans)
    story.append(Spacer(1, 12))

    nota_legal = """<i><b>Nota importante:</b><br/>
    1.- La empresa Venezuela Productiva no se hace responsable de daños ocasionados a productos en el traslado del mismo.<br/>
    2.- Cualquier sustracción o deterioration que no conste en la presente guía, reclame al conductor de inmediato.<br/>
    3.- Favor devolver el duplicado de la guía firmado como garantía de recepción conforme.</i>
    """
    story.append(Paragraph(nota_legal, normal_style))
    story.append(Spacer(1, 35))

    data_firmas = [
        ["_________________________", "_________________________", "_________________________"],
        ["ELABORADO POR (Almacén)", "Conductor / Transportista", "Beneficiario / Autorizado"],
        [f"Usuario: {despacho.responsable.get_full_name() or despacho.responsable.username}", f"C.I.: {despacho.cedula_conductor or '-'}", f"C.I.: {despacho.cedula_beneficiario or '-'}"]
    ]
    table_firmas = Table(data_firmas, colWidths=[183, 183, 184])
    table_firmas.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,1), (-1,1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,0), 2),
    ]))
    story.append(table_firmas)

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    
    response.write(pdf)
    return response


@login_required
def crear_nota_devolucion(request):
    """
    Vista provisional para el registro formal de Notas de Devolución 
    del Almacén Fuerte Tiuna.
    """
    return render(request, 'core/dashboard.html', {
        'mensaje_informativo': 'Módulo de Devoluciones en Fase de Acoplamiento de Interfaz.'
    })


@login_required
def crear_cliente(request):
    """Vista para registrar un nuevo Ente, Institución o Cliente de Proyecto"""
    if request.method == 'POST':
        from django import forms
        class ClienteFormInm(forms.ModelForm):
            class Meta:
                model = Cliente
                fields = ['nombre', 'rif_nit', 'telefono', 'email', 'direccion']
        
        form = ClienteFormInm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('core:crear_cotizacion')
    else:
        from django import forms
        class ClienteFormInm(forms.ModelForm):
            class Meta:
                model = Cliente
                fields = ['nombre', 'rif_nit', 'telefono', 'email', 'direccion']
        form = ClienteFormInm()
        
    return render(request, 'core/cliente_form.html', {'form': form})


@login_required
def crear_proveedor(request):
    """Vista para registrar un nuevo Proveedor de insumos del Almacén"""
    if request.method == 'POST':
        from django import forms
        class ProveedorFormInm(forms.ModelForm):
            class Meta:
                model = Proveedor
                fields = ['nombre', 'rif_nit', 'telefono', 'email', 'direccion']
                
        form = ProveedorFormInm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('core:dashboard')
    else:
        from django import forms
        class ProveedorFormInm(forms.ModelForm):
            class Meta:
                model = Proveedor
                fields = ['nombre', 'rif_nit', 'telefono', 'email', 'direccion']
        form = ProveedorFormInm()
        
    return render(request, 'core/proveedor_form.html', {'form': form})

@login_required
def crear_almacen(request):
    """Vista para registrar un nuevo espacio físico o depósito de inventario"""
    if request.method == 'POST':
        from django import forms
        class AlmacenFormInm(forms.ModelForm):
            class Meta:
                model = Almacen
                # SANEADO: Eliminado codigo_interno que no existe en el modelo
                fields = ['nombre', 'ubicacion'] 
                
        form = AlmacenFormInm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('core:dashboard')
    else:
        from django import forms
        class AlmacenFormInm(forms.ModelForm):
            class Meta:
                model = Almacen
                fields = ['nombre', 'ubicacion']
        form = AlmacenFormInm()
        
    return render(request, 'core/almacen_form.html', {'form': form})

from django.http import JsonResponse

@login_required
def api_productos_cotizacion(request, cotizacion_id):
    """Devuelve los renglones de una cotización para la automatización del despacho"""
    cotizacion = get_object_or_404(Cotizacion, id=cotizacion_id)
    items = cotizacion.items.select_related('producto').all()
    
    data = []
    for item in items:
        data.append({
            'id_item_cotizacion': item.id,
            'producto_id': item.producto.id,
            'producto_nombre': f"[{item.producto.codigo_sku}] {item.producto.nombre}",
            'seccion': item.seccion_departamento,
            'cantidad_pendiente': float(item.cantidad_faltante),
        })
    return JsonResponse({'items': data})

import openpyxl

@login_required
def carga_masiva_productos(request):
    """Vista avanzada para procesar .xlsx guardando montos y asociando almacenes automáticos"""
    context = {'errores': [], 'exitos': 0}
    
    if request.method == 'POST' and request.FILES.get('archivo_xlsx'):
        archivo = request.FILES['archivo_xlsx']
        
        if not archivo.name.endswith('.xlsx'):
            context['errores'].append("El archivo debe tener extensión .xlsx de forma obligatoria.")
            return render(request, 'core/carga_masiva_form.html', context)
            
        try:
            wb = openpyxl.load_workbook(archivo, data_only=True)
            hoja = wb.active
            
            fila_encabezados = None
            num_fila_encabezados = 0
            
            for row in hoja.iter_rows(min_row=1, max_row=15, values_only=True):
                num_fila_encabezados += 1
                headers = [str(c).strip().upper() for c in row if c is not None]
                if 'CODIGO' in headers or 'DESCRIPCION' in headers:
                    fila_encabezados = [str(c).strip().upper() if c is not None else "" for c in row]
                    break
            
            if not fila_encabezados:
                context['errores'].append("No se encontró la fila de encabezados con 'CODIGO' y 'DESCRIPCION'.")
                return render(request, 'core/carga_masiva_form.html', context)
                
            col_map = {idx: name for idx, name in enumerate(fila_encabezados) if name}
            
            conteo_exitos = 0
            with transaction.atomic():
                for nro_fila, row in enumerate(hoja.iter_rows(min_row=num_fila_encabezados + 1, values_only=True), start=num_fila_encabezados + 1):
                    
                    fila_dict = {}
                    for idx, val in enumerate(row):
                        header_name = col_map.get(idx)
                        if header_name:
                            fila_dict[header_name] = val
                    
                    nombre = str(fila_dict.get('DESCRIPCION', '') or fila_dict.get('DESCRIPCION DEL PRODUCTO', '') or '').strip()
                    if not nombre or nombre == 'None' or "TOTAL" in nombre.upper():
                        continue

                    codigo = str(fila_dict.get('CODIGO', '') or '').strip()
                    stock_raw = fila_dict.get('INVENTARIO', fila_dict.get('CANTIDADES', fila_dict.get('ENTRADA', 0)))
                    codigo_oddo = str(fila_dict.get('CODIGO ODDO', '') or '').strip()
                    costo_raw = fila_dict.get('COSTO', fila_dict.get('COSTO_COMPRA', fila_dict.get('PRECIO UNITARIO', 0)))
                    venta_raw = fila_dict.get('PRECIO', fila_dict.get('PRECIO_VENTA', fila_dict.get('MONTO_VENTA', 0)))
                    
                    # 🏢 CAPTURA DE LA COLUMNA ALMACÉN REAL DE LA HOJA
                    almacen_raw = str(fila_dict.get('ALMACEN', '') or fila_dict.get('ALMACÉN', '') or 'LA URBINA').strip()

                    sku_final = codigo if codigo and codigo != 'None' else codigo_oddo
                    if not sku_final or sku_final == 'None':
                        sku_final = f"GEN-{nro_fila}"

                    # Procesamiento numérico seguro
                    def sanear_numero(val):
                        if val is None or str(val).strip() == 'None': return 0.00
                        try: return float(str(val).replace(',', '.'))
                        except ValueError: return 0.00

                    stock_val = sanear_numero(stock_raw)
                    costo_val = sanear_numero(costo_raw)
                    venta_val = sanear_numero(venta_raw)

                    # 🛡️ GESTIÓN ATÓMICA DEL ALMACÉN: Si no existe en el catálogo maestro, se crea solo
                    almacen_instancia = None
                    if almacen_raw and almacen_raw != 'None':
                        almacen_instancia, _ = Almacen.objects.get_or_create(
                            nombre=almacen_raw,
                            defaults={'ubicacion': 'Registrado vía Carga Masiva', 'activo': True}
                        )

                    # Guardar, Actualizar y Vincular a la sede correspondiente
                    Producto.objects.update_or_create(
                        codigo_sku=sku_final,
                        defaults={
                            'nombre': nombre,
                            'descripcion': f"Código Odoo: {codigo_oddo}" if codigo_oddo and codigo_oddo != 'None' else "Cargado masivamente",
                            'stock_actual': stock_val,
                            'costo_compra': costo_val,
                            'precio_venta': venta_val,
                            'almacen': almacen_instancia, # <--- ENLAZADO DIRECTO
                            'activo': True
                        }
                    )
                    conteo_exitos += 1
            
            context['exitos'] = conteo_exitos
            
        except Exception as e:
            context['errores'].append(f"Error crítico procesando celdas: {str(e)}")

    return render(request, 'core/carga_masiva_form.html', context)