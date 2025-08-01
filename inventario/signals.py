# inventario/signals.py

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import DetalleActaRecepcion, Producto, Movimiento
from django.utils import timezone

@receiver(post_save, sender=DetalleActaRecepcion)
def update_product_stock_on_acta_recepcion_save(sender, instance, created, **kwargs):
    """
    Actualiza el stock del producto y crea un registro de movimiento
    cuando se guarda un DetalleActaRecepcion.
    """
    if instance.producto:
        # Obtener la cantidad original si se está actualizando una instancia existente
        original_quantity = 0
        if not created:
            try:
                # Recuperar la instancia original de la base de datos para obtener la cantidad anterior
                original_instance = sender.objects.get(pk=instance.pk)
                original_quantity = original_instance.cantidad
            except sender.DoesNotExist:
                pass # Esto no debería ocurrir si es una actualización

        quantity_change = instance.cantidad - original_quantity

        # Actualizar el stock del producto
        instance.producto.cantidad += quantity_change
        instance.producto.save(update_fields=['cantidad'])

        # Crear un registro de movimiento
        Movimiento.objects.create(
            producto=instance.producto,
            tipo='entrada', # Siempre 'entrada' para ActaRecepcion
            cantidad=abs(quantity_change), # Registrar la cantidad neta del cambio
            descripcion=f"Recepción de {instance.cantidad} unidades de {instance.producto.nombre} vía Acta de Recepción #{instance.acta_recepcion.numero_acta}",
            fecha=timezone.now(),
            acta_recepcion=instance.acta_recepcion # Enlazar al ActaRecepcion
        )

@receiver(post_delete, sender=DetalleActaRecepcion)
def update_product_stock_on_acta_recepcion_delete(sender, instance, **kwargs):
    """
    Revierte el stock del producto y crea un registro de movimiento
    cuando se elimina un DetalleActaRecepcion.
    """
    if instance.producto:
        # Revertir el stock del producto
        instance.producto.cantidad -= instance.cantidad
        instance.producto.save(update_fields=['cantidad'])

        # Crear un registro de movimiento para la reversión
        Movimiento.objects.create(
            producto=instance.producto,
            tipo='salida', # La reversión es una 'salida'
            cantidad=instance.cantidad,
            descripcion=f"Reversión de recepción de {instance.cantidad} unidades de {instance.producto.nombre} (eliminación de Detalle Acta Recepción #{instance.pk} de Acta #{instance.acta_recepcion.numero_acta})",
            fecha=timezone.now(),
            acta_recepcion=instance.acta_recepcion # Enlazar al ActaRecepcion
        )
