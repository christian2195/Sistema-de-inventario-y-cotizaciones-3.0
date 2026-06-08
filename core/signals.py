from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Sum
from .models import ItemDespacho, MovimientoInventario

@receiver(post_save, sender=ItemDespacho)
def procesar_despacho(sender, instance, created, **kwargs):
    if created:
        # 1. Descontar el stock real del producto
        producto = instance.item_cotizacion.producto
        producto.stock_actual -= instance.cantidad_despachada
        producto.save()
        
        # 2. Registrar la trazabilidad inalterable en MovimientoInventario
        MovimientoInventario.objects.create(
            producto=producto,
            almacen=instance.almacen_origen,
            tipo='SALIDA',
            cantidad=instance.cantidad_despachada,
            responsable=instance.nota_despacho.responsable,
            observacion=f"Despacho autogenerado por Guía {instance.nota_despacho.numero_guia}"
        )
        
        # 3. Evaluar el Estatus de la Cotización (El Pilar 4)
        cotizacion = instance.nota_despacho.cotizacion
        todos_items = cotizacion.items.all()
        
        completado = True
        for item in todos_items:
            total_despachado = item.despachos.aggregate(total=Sum('cantidad_despachada'))['total'] or 0
            if total_despachado < item.cantidad_solicitada:
                completado = False
                break
                
        if completado:
            cotizacion.estatus = 'DOTADO'
        else:
            cotizacion.estatus = 'EN_PROCESO'
            
        cotizacion.save()