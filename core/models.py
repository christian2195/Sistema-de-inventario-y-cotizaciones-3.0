from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid
from itertools import groupby

class Proveedor(models.Model):
    nombre = models.CharField(max_length=200)
    rif_nit = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="RIF/NIT",
        help_text="Número de identificación fiscal"
    )
    contacto_principal = models.CharField(max_length=100, blank=True, default='')
    email = models.EmailField(blank=True, default='')
    telefono = models.CharField(max_length=50, blank=True, default='')
    direccion = models.TextField(blank=True, default='')
    fecha_creacion = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        verbose_name_plural = "Proveedores"
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['rif_nit']),
        ]

    def __str__(self):
        return f"{self.nombre} ({self.rif_nit})"


class Cliente(models.Model):
    nombre = models.CharField(max_length=200)
    rif_nit = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="RIF/NIT",
        help_text="Número de identificación fiscal"
    )
    contacto_principal = models.CharField(max_length=100, blank=True, default='')
    email = models.EmailField(blank=True, default='')
    telefono = models.CharField(max_length=50, blank=True, default='')
    direccion = models.TextField(blank=True, default='')
    fecha_creacion = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        verbose_name_plural = "Clientes"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.rif_nit})"


class Almacen(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    ubicacion = models.CharField(max_length=255, blank=True, default='')
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Almacenes"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    codigo_sku = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Código/SKU"
    )
    imagen = models.ImageField(upload_to='productos/', null=True, blank=True, verbose_name="Imagen Referencial")
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, default='')
    stock_actual = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    costo_compra = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        verbose_name="Costo de Compra (USD)",
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    precio_venta = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        verbose_name="Precio de Venta (USD)",
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    almacen = models.ForeignKey(
        Almacen,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='productos'
    )
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Productos"
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['codigo_sku']),
            models.Index(fields=['almacen', 'activo']),
        ]

    def __str__(self):
        return f"[{self.codigo_sku}] {self.nombre} - Costo: ${self.costo_compra} | P.Venta: ${self.precio_venta}"


class Cotizacion(models.Model):
    ESTATUS_CHOICES = [
        ('PENDIENTE', 'Pendiente por despachar'),
        ('EN_PROCESO', 'En Proceso (Parcialmente Dotado)'),
        ('DOTADO', 'Dotado (Completado)'),
        ('ANULADO', 'Anulado'),
    ]
    
    # NUEVAS OPCIONES PARA EL SELECTOR DE PDF
    FORMATO_CHOICES = [
        ('ESTANDAR', 'Estándar (Agrupado por Área)'),
        ('SUBTOTALES', 'Formato 2 (Con Subtotales por Área)'),
    ]

    cliente = models.ForeignKey(
        'Cliente',
        on_delete=models.PROTECT,
        related_name='cotizaciones'
    )
    numero_rastreo = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        verbose_name="Nro. Nota de Entrega / Cotización",
        editable=False
    )
    referencia_proyecto = models.CharField(max_length=255, blank=True, default='')
    fecha_emision = models.DateTimeField(auto_now_add=True, editable=False)
    estatus = models.CharField(
        max_length=20,
        choices=ESTATUS_CHOICES,
        default='PENDIENTE',
        db_index=True
    )
    
    # NUEVO CAMPO PARA DEFINIR EL ESTILO DEL PDF
    formato_pdf = models.CharField(
        max_length=20, 
        choices=FORMATO_CHOICES, 
        default='ESTANDAR', 
        verbose_name="Formato de PDF"
    )

    tasa_bcv = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=1.0000,
        verbose_name="Tasa Cambio BCV",
        validators=[MinValueValidator(Decimal('0.0001'))]
    )
    observacion_tasa = models.CharField(max_length=100, default="BCV")
    incluye_iva = models.BooleanField(default=True, verbose_name="¿Aplica IVA (16%)?")
    subtotal_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    base_imponible_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    monto_iva_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_bs = models.DecimalField(max_digits=16, decimal_places=2, default=0.00)
    observaciones = models.TextField(blank=True, default='')

    class Meta:
        verbose_name_plural = "Cotizaciones"
        ordering = ['-fecha_emision']
        indexes = [
            models.Index(fields=['numero_rastreo']),
            models.Index(fields=['estatus', 'fecha_emision']),
        ]

    def calcular_totales_reales(self):
        items_cot = self.items.all()
        # Sumatoria segura usando Decimal
        self.subtotal_usd = sum(
            (Decimal(str(item.total_item_usd or '0.00')) for item in items_cot),
            Decimal('0.00')
        )
        self.base_imponible_usd = self.subtotal_usd

        if self.incluye_iva:
            self.monto_iva_usd = self.base_imponible_usd * Decimal('0.16')
        else:
            self.monto_iva_usd = Decimal('0.00')

        self.total_usd = self.base_imponible_usd + self.monto_iva_usd

        tasa = Decimal(str(self.tasa_bcv or '1.0000'))
        self.total_bs = self.total_usd * tasa

    def save(self, *args, **kwargs):
        if not self.numero_rastreo:
            self.numero_rastreo = f"COT-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.numero_rastreo} - {self.cliente.nombre}"


# EL MODELO ItemCotizacion QUEDA EXACTAMENTE IGUAL
class ItemCotizacion(models.Model):
    cotizacion = models.ForeignKey(
        Cotizacion,
        on_delete=models.CASCADE,
        related_name='items'
    )
    seccion_departamento = models.CharField(
        max_length=150,
        default="GENERAL"
    )
    producto = models.ForeignKey(
        'Producto',
        on_delete=models.PROTECT
    )
    cantidad_solicitada = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    costo_base_usd = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text="Costo de compra del producto en el momento de la cotización"
    )
    factor_margen = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.10,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Margen sobre el costo (ej. 0.10 = 10%)"
    )
    pvp_unitario_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_item_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    cantidad_entregada = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    cantidad_faltante = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    observacion_item = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        verbose_name_plural = "Ítems de Cotización"
        ordering = ['producto__nombre']

    def clean(self):
        if self.cantidad_entregada > self.cantidad_solicitada:
            raise ValidationError("La cantidad entregada no puede superar la solicitada")

    def save(self, *args, **kwargs):
        if not self.pk and self.costo_base_usd == Decimal('0.00'):
            self.costo_base_usd = self.producto.costo_compra

        costo = Decimal(str(self.costo_base_usd or '0.00'))
        margen = Decimal(str(self.factor_margen or '0.00'))
        cant_sol = Decimal(str(self.cantidad_solicitada or '0.00'))
        cant_ent = Decimal(str(self.cantidad_entregada or '0.00'))

        if costo > Decimal('0.00'):
            self.pvp_unitario_usd = costo * (Decimal('1.00') + margen)

        pvp_uni = Decimal(str(self.pvp_unitario_usd or '0.00'))
        self.total_item_usd = cant_sol * pvp_uni
        self.cantidad_faltante = max(cant_sol - cant_ent, Decimal('0.00'))

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.producto.nombre} - Cant: {self.cantidad_solicitada}"


@receiver(post_save, sender=ItemCotizacion)
def actualizar_totales_cotizacion(sender, instance, **kwargs):
    instance.cotizacion.calcular_totales_reales()
    instance.cotizacion.save(update_fields=[
        'subtotal_usd', 'base_imponible_usd', 'monto_iva_usd',
        'total_usd', 'total_bs'
    ])


class ActaRecepcion(models.Model):
    ESTADO_MERCANCIA_CHOICES = [
        ('BUENO', 'Buen Estado'),
        ('CON_OBSERVACIONES', 'Con Observaciones'),
    ]
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.PROTECT,
        related_name='actas_recepcion'
    )
    almacen = models.ForeignKey(
        Almacen,
        on_delete=models.PROTECT,
        related_name='actas_recepcion'
    )
    numero_factura_proveedor = models.CharField(max_length=100)
    monto_total_factura = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    fecha_recepcion = models.DateTimeField(auto_now_add=True, editable=False)
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT
    )
    institucion = models.CharField(max_length=200, blank=True, default='')
    nro_orden_asociada = models.CharField(max_length=100, blank=True, default='')
    ubicacion_almacen = models.CharField(max_length=100, blank=True, default='')
    estado_mercancia = models.CharField(
        max_length=50,
        choices=ESTADO_MERCANCIA_CHOICES,
        default='BUENO'
    )
    nombre_conductor = models.CharField(max_length=150, blank=True, default='')
    cedula_conductor = models.CharField(max_length=20, blank=True, default='')
    tipo_vehiculo = models.CharField(max_length=100, blank=True, default='')
    color_vehiculo = models.CharField(max_length=50, blank=True, default='')
    placa_vehiculo = models.CharField(max_length=50, blank=True, default='')
    beneficiario_autorizado = models.CharField(max_length=150, blank=True, default='')
    cedula_beneficiario = models.CharField(max_length=20, blank=True, default='')
    telefono_beneficiario = models.CharField(max_length=50, blank=True, default='')
    fecha_hora_llegada_conductor = models.DateTimeField(blank=True, null=True)
    fecha_hora_llegada_beneficiario = models.DateTimeField(blank=True, null=True)
    observaciones = models.TextField(blank=True, default='')

    class Meta:
        verbose_name_plural = "Actas de Recepción"
        ordering = ['-fecha_recepcion']
        indexes = [
            models.Index(fields=['proveedor', 'fecha_recepcion']),
        ]

    def __str__(self):
        return f"Acta #{self.pk} - {self.proveedor.nombre} - {self.numero_factura_proveedor}"


class NotaDespacho(models.Model):
    cotizacion = models.ForeignKey(
        Cotizacion,
        on_delete=models.PROTECT,
        related_name='notas_despacho'
    )
    numero_guia = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Nro. Guía / Despacho",
        editable=False
    )
    fecha_despacho = models.DateTimeField(auto_now_add=True, editable=False)
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT
    )
    nombre_beneficiario = models.CharField(max_length=200, blank=True, default='')
    proveedor_origen = models.CharField(max_length=200, blank=True, default='')
    nro_orden_asociada = models.CharField(max_length=100, blank=True, default='')
    nombre_conductor = models.CharField(max_length=150, blank=True, default='')
    cedula_conductor = models.CharField(max_length=20, blank=True, default='')
    tipo_vehiculo = models.CharField(max_length=100, blank=True, default='')
    color_vehiculo = models.CharField(max_length=50, blank=True, default='')
    placa_vehiculo = models.CharField(max_length=50, blank=True, default='')
    beneficiario_autorizado = models.CharField(max_length=150, blank=True, default='')
    cedula_beneficiario = models.CharField(max_length=20, blank=True, default='')
    telefono_beneficiario = models.CharField(max_length=50, blank=True, default='')
    fecha_hora_llegada_conductor = models.DateTimeField(blank=True, null=True)
    fecha_hora_llegada_beneficiario = models.DateTimeField(blank=True, null=True)
    observaciones = models.TextField(blank=True, default='')

    class Meta:
        verbose_name_plural = "Notas de Despacho"
        ordering = ['-fecha_despacho']

    def save(self, *args, **kwargs):
        if not self.numero_guia:
            self.numero_guia = f"DESP-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Despacho {self.numero_guia} - {self.cotizacion.cliente.nombre}"


class ItemDespacho(models.Model):
    nota_despacho = models.ForeignKey(
        NotaDespacho,
        on_delete=models.CASCADE,
        related_name='items'
    )
    item_cotizacion = models.ForeignKey(
        ItemCotizacion,
        on_delete=models.PROTECT,
        related_name='despachos'
    )
    cantidad_despachada = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    almacen_origen = models.ForeignKey(
        Almacen,
        on_delete=models.PROTECT
    )
    marca = models.CharField(max_length=100, blank=True, default='')
    modelo = models.CharField(max_length=100, blank=True, default='')

    class Meta:
        verbose_name_plural = "Ítems de Despacho"

    def __str__(self):
        return f"{self.item_cotizacion.producto.nombre} - {self.cantidad_despachada} despachado"


class NotaDevolucion(models.Model):
    # Devoluciones a proveedores (logística inversa)
    nro_devolucion = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        editable=False
    )
    fecha_devolucion = models.DateTimeField(auto_now_add=True, editable=False)
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.PROTECT,
        related_name='devoluciones'
    )
    origen_devolucion = models.CharField(
        max_length=200,
        blank=True,
        default='',
        help_text="Motivo o documento origen de la devolución"
    )
    motivo_devolucion = models.TextField(blank=True, default='')
    observaciones = models.TextField(blank=True, default='')
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT
    )
    # Datos de logística inversa
    nombre_conductor = models.CharField(max_length=150, blank=True, default='')
    cedula_conductor = models.CharField(max_length=20, blank=True, default='')
    placa_vehiculo = models.CharField(max_length=50, blank=True, default='')

    class Meta:
        verbose_name_plural = "Notas de Devolución"
        ordering = ['-fecha_devolucion']

    def save(self, *args, **kwargs):
        if not self.nro_devolucion:
            self.nro_devolucion = f"DEV-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Devolución {self.nro_devolucion} - {self.proveedor.nombre}"


class ItemDevolucion(models.Model):
    ESTADO_FISICO_CHOICES = [
        ('BUENO', 'Bueno'),
        ('DANADO', 'Dañado'),
        ('OBSOLETO', 'Obsoleto'),
    ]
    nota_devolucion = models.ForeignKey(
        NotaDevolucion,
        on_delete=models.CASCADE,
        related_name='items'
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        related_name='items_devueltos'
    )
    almacen_destino = models.ForeignKey(
        Almacen,
        on_delete=models.PROTECT,
        help_text="Almacén que recibe la devolución"
    )
    cantidad_devuelta = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    estado_fisico = models.CharField(
        max_length=50,
        choices=ESTADO_FISICO_CHOICES,
        default='BUENO'
    )
    motivo = models.TextField()

    class Meta:
        verbose_name_plural = "Ítems de Devolución"

    def __str__(self):
        return f"{self.producto.nombre} - {self.cantidad_devuelta} devuelto ({self.estado_fisico})"


class MovimientoInventario(models.Model):
    TIPO_CHOICES = [
        ('ENTRADA', 'Entrada'),
        ('SALIDA', 'Salida'),
        ('AJUSTE', 'Ajuste manual'),
        ('DEVOLUCION', 'Devolución'),
    ]
    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        related_name='movimientos'
    )
    almacen = models.ForeignKey(
        Almacen,
        on_delete=models.PROTECT,
        related_name='movimientos'
    )
    tipo = models.CharField(
        max_length=15,
        choices=TIPO_CHOICES,
        db_index=True
    )
    cantidad = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    costo_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    fecha_movimiento = models.DateTimeField(auto_now_add=True, editable=False)
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT
    )
    acta_recepcion = models.ForeignKey(
        ActaRecepcion,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    nota_despacho = models.ForeignKey(
        NotaDespacho,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    nota_devolucion = models.ForeignKey(
        NotaDevolucion,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    observacion = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        verbose_name_plural = "Movimientos de Inventario"
        ordering = ['-fecha_movimiento']
        indexes = [
            models.Index(fields=['producto', 'almacen', '-fecha_movimiento']),
            models.Index(fields=['tipo']),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.producto.nombre} x{self.cantidad} ({self.fecha_movimiento.strftime('%d/%m/%Y %H:%M')})"


class PagoProveedor(models.Model):
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.PROTECT,
        related_name='pagos'
    )
    monto_pagado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    fecha_pago = models.DateTimeField(auto_now_add=True, editable=False)
    referencia_pago = models.CharField(max_length=100)
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT
    )
    observaciones = models.TextField(blank=True, default='')

    class Meta:
        verbose_name_plural = "Pagos a Proveedores"
        ordering = ['-fecha_pago']

    def __str__(self):
        return f"Pago {self.referencia_pago} - {self.proveedor.nombre} por ${self.monto_pagado}"