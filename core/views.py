from django.shortcuts import render
from django.db.models import Sum, F, FloatField
from django.db.models.functions import Coalesce
from .models import Cotizacion, Proveedor, Cliente, ItemCotizacion

# Proyecto: EMVEPRO
# Autor: Gerencia de Tecnología de la Información y Comunicación

def dashboard_principal(request):
    """Pilar 5: Dashboard Mejorado - Salud general del negocio"""
    
    # 1. Calcular Cuentas por Cobrar (Monto total de cotizaciones activas)
    total_por_cobrar = ItemCotizacion.objects.exclude(
        cotizacion__estatus='ANULADO'
    ).aggregate(
        total=Coalesce(Sum(F('cantidad_solicitada') * F('precio_unitario'), output_field=FloatField()), 0.0)
    )['total']

    # 2. Métricas rápidas de operatividad
    metricas = {
        'total_cotizaciones': Cotizacion.objects.count(),
        'en_proceso': Cotizacion.objects.filter(estatus='EN_PROCESO').count(),
        'dotadas': Cotizacion.objects.filter(estatus='DOTADO').count(),
        'pendientes': Cotizacion.objects.filter(estatus='PENDIENTE').count(),
    }

    context = {
        'total_por_cobrar': round(total_por_cobrar, 2),
        'metricas': metricas,
    }
    return render(request, 'core/dashboard.html', context)


def estatus_proyectos(request):
    """Pilar 4: Interfaz de Estatus de Proyectos (Porcentaje de dotación en tiempo real)"""
    
    # Traemos las cotizaciones pre-cargando sus ítems y despachos para no saturar la base de datos
    cotizaciones = Cotizacion.objects.exclude(estatus='ANULADO').prefetch_related('items__despachos')
    
    proyectos_data = []
    for cot in cotizaciones:
        total_solicitado = 0
        total_despachado = 0
        
        # Cruzamos lo solicitado vs lo despachado iterando sobre los ítems
        for item in cot.items.all():
            total_solicitado += item.cantidad_solicitada
            despachado_item = sum(despacho.cantidad_despachada for despacho in item.despachos.all())
            total_despachado += despachado_item
            
        # Calculamos el porcentaje exacto
        if total_solicitado > 0:
            porcentaje = (total_despachado / total_solicitado) * 100
        else:
            porcentaje = 0
            
        proyectos_data.append({
            'numero_rastreo': cot.numero_rastreo,
            'cliente': cot.cliente.nombre,
            'estatus': cot.get_estatus_display(),
            'porcentaje_dotacion': round(porcentaje, 2),
        })
        
    context = {
        'proyectos': proyectos_data
    }
    return render(request, 'core/estatus_proyectos.html', context)