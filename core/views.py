from django.contrib.auth.decorators import login_required
from django.shortcuts import render,redirect
from django.db.models import Sum, F, FloatField
from django.db.models.functions import Coalesce
from .models import Cotizacion, Proveedor, Cliente, ItemCotizacion, ActaRecepcion, PagoProveedor, Producto
from .forms import ProductoForm, CotizacionForm, ItemCotizacionFormSet, ActaRecepcionForm, MovimientoRecepcionFormSet, NotaDespachoForm, ItemDespachoFormSet
from django.db import transaction
from django.http import HttpResponse
from django.template.loader import get_template
from django.shortcuts import get_object_or_404
from xhtml2pdf import pisa

# Proyecto: EMVEPRO
# Autor: Gerencia de Tecnología de la Información y Comunicación

@login_required
def dashboard_principal(request):
    """Pilar 5: Dashboard Mejorado - Salud general del negocio"""
    
    # 1. Calcular Cuentas por Cobrar (Monto total de cotizaciones activas)
    total_por_cobrar = ItemCotizacion.objects.exclude(
        cotizacion__estatus='ANULADO'
    ).aggregate(
        total=Coalesce(Sum(F('cantidad_solicitada') * F('precio_unitario'), output_field=FloatField()), 0.0)
    )['total']

    # 2. Calcular Deuda con Proveedores (Facturado vs Pagado)
    total_facturado = ActaRecepcion.objects.aggregate(
        total=Coalesce(Sum('monto_total_factura', output_field=FloatField()), 0.0)
    )['total']
    
    total_pagado = PagoProveedor.objects.aggregate(
        total=Coalesce(Sum('monto_pagado', output_field=FloatField()), 0.0)
    )['total']
    
    deuda_proveedores = total_facturado - total_pagado

    # 3. Métricas rápidas de operatividad
    metricas = {
        'total_cotizaciones': Cotizacion.objects.count(),
        'en_proceso': Cotizacion.objects.filter(estatus='EN_PROCESO').count(),
        'dotadas': Cotizacion.objects.filter(estatus='DOTADO').count(),
        'pendientes': Cotizacion.objects.filter(estatus='PENDIENTE').count(),
    }

    context = {
        'total_por_cobrar': round(total_por_cobrar, 2),
        'deuda_proveedores': round(deuda_proveedores, 2),
        'metricas': metricas,
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
            'id': cot.id,  # <--- NUEVA LÍNEA AGREGADA
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
        # Sumamos lo que nos han facturado en Actas de Recepción
        facturado = prov.actas_recepcion.aggregate(total=Coalesce(Sum('monto_total_factura', output_field=FloatField()), 0.0))['total']
        # Sumamos lo que les hemos pagado
        pagado = prov.pagos.aggregate(total=Coalesce(Sum('monto_pagado', output_field=FloatField()), 0.0))['total']
        
        deuda = facturado - pagado

        # Solo enviamos a la vista los proveedores con los que hemos tenido movimientos
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
    """Muestra el catálogo de productos de EMVEPRO"""
    productos = Producto.objects.all().order_by('nombre')
    return render(request, 'core/producto_list.html', {'productos': productos})


@login_required
def crear_producto(request):
    """Renderiza y procesa el formulario para crear un nuevo producto"""
    if request.method == 'POST':
        # Si el usuario envió los datos, los pasamos al formulario
        form = ProductoForm(request.POST)
        if form.is_valid():
            form.save() # Guarda en la base de datos automáticamente
            return redirect('core:lista_productos') # Lo devolvemos a la lista
    else:
        # Si entra por primera vez, mostramos el formulario vacío
        form = ProductoForm()
    
    return render(request, 'core/producto_form.html', {'form': form})


@login_required
def crear_cotizacion(request):
    """Genera una cotización y todos sus ítems en un solo paso"""
    if request.method == 'POST':
        form = CotizacionForm(request.POST)
        formset = ItemCotizacionFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            # transaction.atomic garantiza que todo se guarde o nada se guarde si hay error
            with transaction.atomic():
                cotizacion = form.save()
                # Le decimos al formset a qué cotización pertenecen estos ítems
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
                # 1. Guardamos el acta base
                acta = form.save()
                
                # 2. Guardamos los movimientos pero le decimos a Django que espere un momento (commit=False)
                movimientos = formset.save(commit=False)
                
                for mov in movimientos:
                    # Heredamos los datos del acta padre al movimiento hijo
                    mov.acta_recepcion = acta
                    mov.almacen = acta.almacen
                    mov.responsable = acta.responsable
                    mov.tipo = 'ENTRADA'
                    mov.save() # Ahora sí guardamos el movimiento
                    
                    # 3. Sumamos la cantidad al stock del producto
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
    """Genera una Guía de Salida y detona automáticamente las señales de inventario"""
    if request.method == 'POST':
        form = NotaDespachoForm(request.POST)
        formset = ItemDespachoFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                despacho = form.save()
                formset.instance = despacho
                formset.save()
                # NOTA: Al ejecutar formset.save(), se crean los ItemDespacho en la BD.
                # Esto dispara inmediatamente la señal en signals.py que resta el stock.
            return redirect('core:estatus_proyectos')
    else:
        form = NotaDespachoForm()
        formset = ItemDespachoFormSet()

    context = {
        'form': form,
        'formset': formset,
    }
    return render(request, 'core/despacho_form.html', context)

@login_required
def generar_pdf_cotizacion(request, cotizacion_id):
    """Genera un documento PDF formal para la cotización seleccionada"""
    cotizacion = get_object_or_404(Cotizacion, id=cotizacion_id)
    
    # Preparamos los datos que irán al PDF
    context = {'cotizacion': cotizacion}
    
    # Buscamos la plantilla HTML
    template = get_template('core/cotizacion_pdf.html')
    html = template.render(context)
    
    # Creamos la respuesta HTTP configurada como PDF
    response = HttpResponse(content_type='application/pdf')
    # attachment; fuerza la descarga. Si quieres que se abra en el navegador usa inline;
    response['Content-Disposition'] = f'inline; filename="Cotizacion_EMVEPRO_{cotizacion.numero_rastreo}.pdf"'
    
    # Convertimos el HTML a PDF
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    if pisa_status.err:
        return HttpResponse('Tuvimos errores generando el PDF', status=500)
    
    return response