from django.db import models
from django.contrib.auth.models import User
import uuid

# Proyecto: EMVEPRO
# Autor: Gerencia de Tecnología de la Información y Comunicación

class Proveedor(models.Model):
    nombre = models.CharField(max_length=200)
    rif_nit = models.CharField(max_length=50, unique=True, verbose_name="RIF/NIT")
    contacto_principal = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Proveedores"

    def __str__(self):
        return f"{self.nombre} ({self.rif_nit})"

class Cliente(models.Model):
    nombre = models.CharField(max_length=200)
    rif_nit = models.CharField(max_length=50, unique=True, verbose_name="RIF/NIT")
    contacto_principal = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} ({self.rif_nit})"

class Almacen(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    ubicacion = models.CharField(max_length=255, blank=True, null=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Almacenes"

    def __str__(self):
        return self.nombre

class Producto(models.Model):
    codigo_sku = models.CharField(max_length=50, unique=True, verbose_name="Código/SKU")
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    # stock_actual es un campo de lectura que se actualizará con Signals en la Fase 2
    stock_actual = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"[{self.codigo_sku}] {self.nombre}"

class ActaRecepcion(models.Model):
    """Pilar 1: Registro formal de la entrada de mercancía"""
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, related_name='actas_recepcion')
    almacen = models.ForeignKey(Almacen, on_delete=models.PROTECT, related_name='actas_recepcion')
    numero_factura_proveedor = models.CharField(max_length=100, help_text="Número de factura o nota de entrega")
    monto_total_factura = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Monto total a pagar por esta recepción")
    fecha_recepcion = models.DateTimeField(auto_now_add=True)
    responsable = models.ForeignKey(User, on_delete=models.PROTECT, help_text="Usuario que recibe la mercancía")
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Actas de Recepción"

    def __str__(self):
        return f"Acta #{self.id} - {self.proveedor.nombre} - {self.fecha_recepcion.strftime('%d/%m/%Y')}"

class MovimientoInventario(models.Model):
    """Pilar 2: Control estricto de entradas y salidas"""
    TIPO_MOVIMIENTO = [
        ('ENTRADA', 'Entrada (Por Recepción)'),
        ('SALIDA', 'Salida (Por Despacho)'),
        ('AJUSTE_POS', 'Ajuste Positivo'),
        ('AJUSTE_NEG', 'Ajuste Negativo'),
    ]

    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='movimientos')
    almacen = models.ForeignKey(Almacen, on_delete=models.PROTECT, related_name='movimientos')
    tipo = models.CharField(max_length=15, choices=TIPO_MOVIMIENTO)
    cantidad = models.DecimalField(max_digits=12, decimal_places=2)
    costo_unitario = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    fecha_movimiento = models.DateTimeField(auto_now_add=True)
    responsable = models.ForeignKey(User, on_delete=models.PROTECT)
    
    # Claves foráneas para cruzar la data (El despacho se conectará en la Fase 2)
    acta_recepcion = models.ForeignKey(ActaRecepcion, on_delete=models.CASCADE, null=True, blank=True, related_name='items_recibidos')
    
    observacion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Movimientos de Inventario"

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.producto.codigo_sku} ({self.cantidad})"

class Cotizacion(models.Model):
    """El núcleo del Pilar 3: Generación de cotizaciones sin descontar stock"""
    ESTATUS_CHOICES = [
        ('PENDIENTE', 'Pendiente por despachar'),
        ('EN_PROCESO', 'En Proceso (Parcialmente Dotado)'),
        ('DOTADO', 'Dotado (Completado)'),
        ('ANULADO', 'Anulado'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='cotizaciones')
    numero_rastreo = models.CharField(max_length=50, unique=True, blank=True)
    fecha_emision = models.DateTimeField(auto_now_add=True)
    estatus = models.CharField(max_length=20, choices=ESTATUS_CHOICES, default='PENDIENTE')
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Cotizaciones"

    def save(self, *args, **kwargs):
        # Generar un número de rastreo automático si no existe
        if not self.numero_rastreo:
            self.numero_rastreo = f"COT-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.numero_rastreo} - {self.cliente.nombre} ({self.get_estatus_display()})"

class ItemCotizacion(models.Model):
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad_solicitada = models.DecimalField(max_digits=12, decimal_places=2)
    # Aquí puedes añadir precio_unitario para la Fase 3 (Módulo Financiero)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    class Meta:
        verbose_name_plural = "Ítems de Cotización"

    def __str__(self):
        return f"{self.cantidad_solicitada}x {self.producto.nombre}"

class NotaDespacho(models.Model):
    """Guías de Salida conectadas a una cotización confirmada"""
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.PROTECT, related_name='notas_despacho')
    numero_guia = models.CharField(max_length=50, unique=True)
    fecha_despacho = models.DateTimeField(auto_now_add=True)
    responsable = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        verbose_name_plural = "Notas de Despacho"

    def __str__(self):
        return f"Guía {self.numero_guia} (Cot: {self.cotizacion.numero_rastreo})"

class ItemDespacho(models.Model):
    """El puente que irá descontando progresivamente los artículos"""
    nota_despacho = models.ForeignKey(NotaDespacho, on_delete=models.CASCADE, related_name='items')
    item_cotizacion = models.ForeignKey(ItemCotizacion, on_delete=models.PROTECT, related_name='despachos')
    cantidad_despachada = models.DecimalField(max_digits=12, decimal_places=2)
    almacen_origen = models.ForeignKey(Almacen, on_delete=models.PROTECT)

    class Meta:
        verbose_name_plural = "Ítems de Despacho"

    def __str__(self):
        return f"{self.cantidad_despachada} despachada de {self.item_cotizacion.producto.nombre}"

class PagoProveedor(models.Model):
    """Registro de pagos emitidos a proveedores para rebajar la deuda"""
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, related_name='pagos')
    monto_pagado = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_pago = models.DateTimeField(auto_now_add=True)
    referencia_pago = models.CharField(max_length=100, help_text="Número de transferencia, cheque o recibo")
    responsable = models.ForeignKey(User, on_delete=models.PROTECT)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Pagos a Proveedores"

    def __str__(self):
        return f"Pago de {self.monto_pagado} a {self.proveedor.nombre} ({self.referencia_pago})"