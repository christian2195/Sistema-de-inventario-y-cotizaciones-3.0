from django.db import models
from django.contrib.auth.models import User
import uuid

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

    class Meta:
        verbose_name_plural = "Clientes"

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
    stock_actual = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    costo_compra = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Costo de Compra (USD)")
    precio_venta = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Precio de Venta (USD)") 
    almacen = models.ForeignKey(Almacen, on_delete=models.SET_NULL, null=True, blank=True, related_name='productos')
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Productos"

    def __str__(self):
        return f"[{self.codigo_sku}] {self.nombre} - Costo: ${self.costo_compra} | P.Venta: ${self.precio_venta}"

class Cotizacion(models.Model):
    ESTATUS_CHOICES = [
        ('PENDIENTE', 'Pendiente por despachar'),
        ('EN_PROCESO', 'En Proceso (Parcialmente Dotado)'),
        ('DOTADO', 'Dotado (Completado)'),
        ('ANULADO', 'Anulado'),
    ]
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='cotizaciones')
    numero_rastreo = models.CharField(max_length=50, unique=True, blank=True, verbose_name="Nro. Nota de Entrega / Cotización")
    referencia_proyecto = models.CharField(max_length=255, blank=True, null=True)
    fecha_emision = models.DateTimeField(auto_now_add=True)
    estatus = models.CharField(max_length=20, choices=ESTATUS_CHOICES, default='PENDIENTE')
    tasa_bcv = models.DecimalField(max_digits=12, decimal_places=4, default=1.0000, verbose_name="Tasa Cambio BCV")
    observacion_tasa = models.CharField(max_length=100, default="BCV")
    incluye_iva = models.BooleanField(default=True, verbose_name="¿Aplica IVA (16%)?")
    subtotal_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    base_imponible_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    monto_iva_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_bs = models.DecimalField(max_digits=16, decimal_places=2, default=0.00)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Cotizaciones"

    def calcular_totales_reales(self):
        items_cot = self.items.all()
        self.subtotal_usd = sum(item.total_item_usd for item in items_cot)
        self.base_imponible_usd = self.subtotal_usd
        if self.incluye_iva:
            self.monto_iva_usd = self.base_imponible_usd * models.Decimal('0.16')
        else:
            self.monto_iva_usd = models.Decimal('0.00')
        self.total_usd = self.base_imponible_usd + self.monto_iva_usd
        self.total_bs = self.total_usd * self.tasa_bcv

    def save(self, *args, **kwargs):
        if not self.numero_rastreo:
            self.numero_rastreo = f"COT-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.numero_rastreo} - {self.cliente.nombre}"

class ItemCotizacion(models.Model):
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name='items')
    seccion_departamento = models.CharField(max_length=150, default="GENERAL")
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad_solicitada = models.DecimalField(max_digits=12, decimal_places=2)
    costo_base_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    factor_margen = models.DecimalField(max_digits=5, decimal_places=2, default=0.10)
    pvp_unitario_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_item_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    cantidad_entregada = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    cantidad_faltante = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    observacion_item = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Ítems de Cotización"

    def save(self, *args, **kwargs):
        if self.costo_base_usd > 0:
            self.pvp_unitario_usd = self.costo_base_usd * (models.Decimal('1.00') + self.factor_margen)
        self.total_item_usd = self.cantidad_solicitada * self.pvp_unitario_usd
        self.cantidad_faltante = self.cantidad_solicitada - self.cantidad_entregada
        super().save(*args, **kwargs)
        self.cotizacion.calcular_totales_reales()
        self.cotizacion.save()

    def __str__(self):
        return f"{self.producto.nombre} - Cant: {self.cantidad_solicitada}"

class ActaRecepcion(models.Model):
    ESTADO_MERCANCIA_CHOICES = [('BUENO', 'Buen Estado'), ('CON_OBSERVACIONES', 'Con Observaciones')]
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, related_name='actas_recepcion')
    almacen = models.ForeignKey(Almacen, on_delete=models.PROTECT, related_name='actas_recepcion')
    numero_factura_proveedor = models.CharField(max_length=100)
    monto_total_factura = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    fecha_recepcion = models.DateTimeField(auto_now_add=True)
    responsable = models.ForeignKey(User, on_delete=models.PROTECT)
    institucion = models.CharField(max_length=200, blank=True, null=True)
    nro_orden_asociada = models.CharField(max_length=100, blank=True, null=True)
    ubicacion_almacen = models.CharField(max_length=100, blank=True, null=True)
    estado_mercancia = models.CharField(max_length=50, choices=ESTADO_MERCANCIA_CHOICES, default='BUENO')
    nombre_conductor = models.CharField(max_length=150, blank=True, null=True)
    cedula_conductor = models.CharField(max_length=20, blank=True, null=True)
    tipo_vehiculo = models.CharField(max_length=100, blank=True, null=True)
    color_vehiculo = models.CharField(max_length=50, blank=True, null=True)
    placa_vehiculo = models.CharField(max_length=50, blank=True, null=True)
    beneficiario_autorizado = models.CharField(max_length=150, blank=True, null=True)
    cedula_beneficiario = models.CharField(max_length=20, blank=True, null=True)
    telefono_beneficiario = models.CharField(max_length=50, blank=True, null=True)
    fecha_hora_llegada_conductor = models.DateTimeField(blank=True, null=True)
    fecha_hora_llegada_beneficiario = models.DateTimeField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Actas de Recepción"

class NotaDespacho(models.Model):
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.PROTECT, related_name='notas_despacho')
    numero_guia = models.CharField(max_length=50, unique=True, verbose_name="Nro. Guía / Despacho")
    fecha_despacho = models.DateTimeField(auto_now_add=True)
    responsable = models.ForeignKey(User, on_delete=models.PROTECT)
    nombre_beneficiario = models.CharField(max_length=200, blank=True, null=True)
    proveedor_origen = models.CharField(max_length=200, blank=True, null=True)
    nro_orden_asociada = models.CharField(max_length=100, blank=True, null=True)
    nombre_conductor = models.CharField(max_length=150, blank=True, null=True)
    cedula_conductor = models.CharField(max_length=20, blank=True, null=True)
    tipo_vehiculo = models.CharField(max_length=100, blank=True, null=True)
    color_vehiculo = models.CharField(max_length=50, blank=True, null=True)
    placa_vehiculo = models.CharField(max_length=50, blank=True, null=True)
    beneficiario_autorizado = models.CharField(max_length=150, blank=True, null=True)
    cedula_beneficiario = models.CharField(max_length=20, blank=True, null=True)
    telefono_beneficiario = models.CharField(max_length=50, blank=True, null=True)
    fecha_hora_llegada_conductor = models.DateTimeField(blank=True, null=True)
    fecha_hora_llegada_beneficiario = models.DateTimeField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Notas de Despacho"

class ItemDespacho(models.Model):
    nota_despacho = models.ForeignKey(NotaDespacho, on_delete=models.CASCADE, related_name='items')
    item_cotizacion = models.ForeignKey(ItemCotizacion, on_delete=models.PROTECT, related_name='despachos')
    cantidad_despachada = models.DecimalField(max_digits=12, decimal_places=2)
    almacen_origen = models.ForeignKey(Almacen, on_delete=models.PROTECT) # <--- RETORNADO COMPLEMENTARIO
    marca = models.CharField(max_length=100, blank=True, null=True)
    modelo = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Ítems de Despacho"

class NotaDevolucion(models.Model):
    nro_devolucion = models.CharField(max_length=50, unique=True)
    origen_devolucion = models.CharField(max_length=200)
    fecha_devolucion = models.DateTimeField(auto_now_add=True)
    motivo_devolucion = models.TextField()
    estado_del_producto = models.CharField(max_length=50, default='APTO')
    nro_orden = models.CharField(max_length=100, blank=True, null=True)
    responsable = models.ForeignKey(User, on_delete=models.PROTECT)
    nombre_conductor = models.CharField(max_length=150, blank=True, null=True)
    cedula_conductor = models.CharField(max_length=20, blank=True, null=True)
    tipo_vehiculo = models.CharField(max_length=100, blank=True, null=True)
    color_vehiculo = models.CharField(max_length=50, blank=True, null=True)
    placa_vehiculo = models.CharField(max_length=50, blank=True, null=True)
    beneficiario_autorizado = models.CharField(max_length=150, blank=True, null=True)
    cedula_beneficiario = models.CharField(max_length=20, blank=True, null=True)
    telefono_beneficiario = models.CharField(max_length=50, blank=True, null=True)
    fecha_hora_llegada_conductor = models.DateTimeField(blank=True, null=True)
    fecha_hora_llegada_beneficiario = models.DateTimeField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Notas de Devolución"

class ItemDevolucion(models.Model):
    nota_devolucion = models.ForeignKey(NotaDevolucion, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='items_devueltos')
    cantidad = models.DecimalField(max_digits=12, decimal_places=2)
    marca = models.CharField(max_length=100, blank=True, null=True)
    modelo = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Ítems de Devolución"

class MovimientoInventario(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='movimientos')
    almacen = models.ForeignKey(Almacen, on_delete=models.PROTECT, related_name='movimientos')
    tipo = models.CharField(max_length=15)
    cantidad = models.DecimalField(max_digits=12, decimal_places=2)
    costo_unitario = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    fecha_movimiento = models.DateTimeField(auto_now_add=True)
    responsable = models.ForeignKey(User, on_delete=models.PROTECT)
    acta_recepcion = models.ForeignKey(ActaRecepcion, on_delete=models.CASCADE, null=True, blank=True)
    nota_despacho = models.ForeignKey(NotaDespacho, on_delete=models.CASCADE, null=True, blank=True)
    nota_devolucion = models.ForeignKey(NotaDevolucion, on_delete=models.CASCADE, null=True, blank=True)
    observacion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Movimientos de Inventario"

class PagoProveedor(models.Model):
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, related_name='pagos')
    monto_pagado = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_pago = models.DateTimeField(auto_now_add=True)
    referencia_pago = models.CharField(max_length=100)
    responsable = models.ForeignKey(User, on_delete=models.PROTECT)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Pagos a Proveedores"
