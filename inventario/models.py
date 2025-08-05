# inventario/models.py

from django.db import models
from django.core.files import File
from io import BytesIO
import qrcode
from PIL import Image, ImageDraw
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
import uuid # Asegúrate de que uuid esté importado aquí
from django.conf import settings
# Función helper para generación de números secuenciales
def generar_numero_secuencial(prefix, last_instance, field_name='numero'):
    if last_instance:
        last_num = int(getattr(last_instance, field_name).split('-')[1])
        return f"{prefix}-{str(last_num + 1).zfill(6)}"
    return f"{prefix}-000001"

# Modelo: Almacen
class Almacen(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre del Almacén")
    ubicacion = models.CharField(max_length=255, blank=True, verbose_name="Ubicación")

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Almacén"
        verbose_name_plural = "Almacenes"

# Modelo: Proveedor
class Proveedor(models.Model):
    nombre = models.CharField(max_length=200, unique=True, verbose_name="Nombre del Proveedor")
    contacto = models.CharField(max_length=255, blank=True, verbose_name="Persona de Contacto")
    telefono = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    email = models.EmailField(blank=True, verbose_name="Email")

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"

# Modelo: UnidadMedida
class UnidadMedida(models.Model):
    nombre = models.CharField(max_length=50, unique=True, verbose_name="Nombre de la Unidad")
    abreviatura = models.CharField(max_length=10, unique=True, verbose_name="Abreviatura")

    def __str__(self):
        return self.abreviatura

    class Meta:
        verbose_name = "Unidad de Medida"
        verbose_name_plural = "Unidades de Medida"

# Modelo: Producto
class Producto(models.Model):
    nombre = models.CharField(max_length=200, db_index=True, verbose_name="Nombre del Producto")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    sku = models.CharField(max_length=100, unique=True, db_index=True, verbose_name="SKU (Código de Artículo)")
    cantidad = models.PositiveIntegerField(default=0, verbose_name="Cantidad en Stock")
    precio = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio")
    foto = models.ImageField(upload_to='productos_fotos/', null=True, blank=True)
    
    foto = models.ImageField(
        upload_to='product_photos/',
        blank=True,
        null=True,
        verbose_name="Foto Referencial"
    )
    
    unidad_medida = models.ForeignKey(UnidadMedida, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Unidad de Medida")
    proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Proveedor Principal")
    almacen = models.ForeignKey(Almacen, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Almacén")
    stock_minimo = models.PositiveIntegerField(default=0, verbose_name="Stock Mínimo")
    
    marca = models.CharField(max_length=100, blank=True, verbose_name="Marca")
    modelo = models.CharField(max_length=100, blank=True, verbose_name="Modelo")

    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de Actualización")

    def __str__(self):
        return f"{self.nombre} ({self.sku})"

    def necesita_reabastecimiento(self):
        return self.cantidad < self.stock_minimo
    
    def clean(self):
        if self.cantidad < 0:
            raise ValidationError("La cantidad en stock no puede ser negativa")
        
    def descontar_stock(self, cantidad_a_descontar):
        if self.cantidad < cantidad_a_descontar:
            raise ValidationError(f"Stock insuficiente para {self.nombre}")
        self.cantidad -= cantidad_a_descontar
        self.save()

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"

# Modelo: Movimiento
class Movimiento(models.Model):
    TIPO_MOVIMIENTO = (
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
    )
    
    producto = models.ForeignKey(
        Producto, 
        on_delete=models.PROTECT,
        related_name='movimientos'
    )
    tipo = models.CharField(max_length=10, choices=TIPO_MOVIMIENTO, verbose_name="Tipo de Movimiento")
    cantidad = models.PositiveIntegerField(verbose_name="Cantidad")
    fecha = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="Fecha del Movimiento")
    descripcion = models.CharField(max_length=255, blank=True, verbose_name="Descripción/Motivo")
    
    guia_salida = models.ForeignKey(
        'GuiaSalida',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimientos_agrupados',
        verbose_name="Guía de Salida Asociada"
    )
    
    acta_recepcion = models.ForeignKey(
        'ActaRecepcion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimientos_agrupados',
        verbose_name="Acta de Recepción Asociada"
    )

    def __str__(self):
        return f'{self.get_tipo_display()} de {self.cantidad} x {self.producto.nombre}'

    def save(self, *args, **kwargs):
        # La lógica de actualización de stock se moverá a las señales para evitar duplicación
        # y asegurar que se dispare correctamente con las operaciones del formset.
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # La lógica de reversión de stock se moverá a las señales.
        super().delete(*args, **kwargs)

    class Meta:
        verbose_name = "Movimiento de Inventario"
        verbose_name_plural = "Movimientos de Inventario"

# Modelo: GuiaSalida
class GuiaSalida(models.Model):
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    destinatario = models.CharField(max_length=255, verbose_name="Destinatario")
    qr_code = models.ImageField(upload_to='qr_codes', blank=True, verbose_name="Código QR")
    
    nota_despacho = models.ForeignKey(
        'NotaDespacho',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='guias_salida_asociadas',
        verbose_name="Nota de Despacho Asociada"
    )
    
    acta_recepcion = models.ForeignKey(
        'ActaRecepcion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='guias_recepcion_asociadas',
        verbose_name="Acta de Recepción Asociada"
    )

    def __str__(self):
        return f'Guía de Salida para {self.destinatario} - {self.fecha_creacion.strftime("%d/%m/%Y")}'

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new and not self.qr_code:
            qr_info = (
                f"Guía de Salida\n"
                f"ID: {self.id}\n"
                f"Fecha: {self.fecha_creacion.strftime('%Y-%m-%d %H:%M')}\n"
                f"Destinatario: {self.destinatario}\n"
                f"Productos: {', '.join(m.producto.nombre for m in self.movimientos_agrupados.all())}"
            )

            qr_image = qrcode.make(qr_info, box_size=10)
            qr_image = qr_image.convert('RGB')

            canvas_width = max(350, qr_image.width + 20)
            canvas_height = max(350, qr_image.height + 20)

            canvas = Image.new('RGB', (canvas_width, canvas_height), 'white')
            x_offset = (canvas_width - qr_image.width) // 2
            y_offset = (canvas_height - qr_image.height) // 2
            canvas.paste(qr_image, (x_offset, y_offset))
            
            fname = f'guia_qr_{self.id}.png'
            buffer = BytesIO()
            canvas.save(buffer, 'PNG')
            
            self.qr_code.save(fname, File(buffer), save=False)
            super().save(update_fields=['qr_code'])

    class Meta:
        verbose_name = "Guía de Salida"
        verbose_name_plural = "Guías de Salida"

# Modelo: NotaDespacho
class NotaDespacho(models.Model):
    numero_despacho = models.CharField(max_length=20, unique=True, blank=True, verbose_name="Nro. Despacho")
    cliente = models.ForeignKey('Cliente', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Cliente")
    fecha_despacho = models.DateField(auto_now_add=True, verbose_name="Fecha de Despacho")
    proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Proveedor")
    orden_asociada = models.CharField(max_length=100, blank=True, verbose_name="N° Orden Asociada")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")
    nombre_conductor = models.CharField(max_length=255, blank=True, verbose_name="Nombre del Conductor")
    ci_conductor = models.CharField(max_length=20, blank=True, verbose_name="C.I. Conductor")
    tipo_vehiculo = models.CharField(max_length=100, blank=True, verbose_name="Tipo de Vehículo")
    color_vehiculo = models.CharField(max_length=50, blank=True, verbose_name="Color del Vehículo")
    placa_vehiculo = models.CharField(max_length=20, blank=True, verbose_name="Placa del Vehículo")
    
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, # Si el usuario se elimina, este campo se pone a NULL
        null=True,                 # Permite que el campo sea nulo en la base de datos
        blank=True,                # Permite que el campo sea opcional en formularios
        related_name='notas_despacho_creadas', # Nombre para la relación inversa
        verbose_name="Creado por"
    )
    orden_salida_referencia = models.ForeignKey(
        'OrdenSalida',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notas_despacho_relacionadas',
        verbose_name="Orden de Salida de Referencia"
    )

    def save(self, *args, **kwargs):
        if not self.numero_despacho:
            last_despacho = NotaDespacho.objects.all().order_by('-id').first()
            self.numero_despacho = generar_numero_secuencial('D', last_despacho, 'numero_despacho')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Nota de Despacho {self.numero_despacho} - {self.cliente}"

    class Meta:
        verbose_name = "Nota de Despacho"
        verbose_name_plural = "Notas de Despacho"

# Modelo: DetalleNotaDespacho
class DetalleNotaDespacho(models.Model):
    nota_despacho = models.ForeignKey('NotaDespacho', on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey('Producto', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Producto")
    nombre_producto_despacho = models.CharField(max_length=200, blank=True, verbose_name="Nombre del Producto (Despacho)")
    marca = models.CharField(max_length=100, blank=True, verbose_name="Marca")
    modelo = models.CharField(max_length=100, blank=True, verbose_name="Modelo")
    cantidad = models.PositiveIntegerField(verbose_name="Cantidad") # Cambiado de cantidad_despachada
    
    detalle_cotizacion_origen = models.ForeignKey(
        'DetalleCotizacion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='detalles_despacho_asociados',
        verbose_name="Detalle de Cotización de Origen"
    )

    class Meta:
        verbose_name = "Detalle de Nota de Despacho"
        verbose_name_plural = "Detalles de Notas de Despacho"

    def __str__(self):
        return f"Despacho {self.cantidad} de {self.nombre_producto_despacho} para {self.nota_despacho.id}"

# Modelo: OrdenSalida
class OrdenSalida(models.Model):
    fecha_orden = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Orden")
    cliente = models.CharField(max_length=255, blank=True, verbose_name="Cliente")
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Total de la Orden")
    
    nota_despacho_asociada = models.OneToOneField(
        NotaDespacho,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orden_salida',
        verbose_name="Nota de Despacho Asociada"
    )
    
    cotizacion_origen = models.ForeignKey(
        'Cotizacion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ordenes_salida',
        verbose_name="Cotización de Origen"
    )

    def __str__(self):
        return f"Orden #{self.id} - {self.cliente} ({self.fecha_orden.strftime('%d/%m/%Y %H:%M')})"

    class Meta:
        verbose_name = "Orden de Salida"
        verbose_name_plural = "Órdenes de Salida"

# Modelo: DetalleOrdenSalida
class DetalleOrdenSalida(models.Model):
    orden_salida = models.ForeignKey(OrdenSalida, on_delete=models.CASCADE, related_name='detalles_orden')
    producto = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Producto")
    cantidad = models.PositiveIntegerField(verbose_name="Cantidad")
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio Unitario")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Subtotal")

    def save(self, *args, **kwargs):
        if not self.subtotal and self.producto and self.cantidad is not None and self.precio_unitario is not None:
            self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre if self.producto else 'N/A'} en Orden #{self.orden_salida.id}"

    class Meta:
        verbose_name = "Detalle de Orden de Salida"
        verbose_name_plural = "Detalles de Órdenes de Salida"

# Modelo: ActaRecepcion
class ActaRecepcion(models.Model):
    ESTADO_ACTA_CHOICES = [
        ('pendiente', 'Pendiente de Procesar'),
        ('parcial', 'Parcialmente Recibida'),
        ('completa', 'Completada'),
        ('cancelada', 'Cancelada'),
    ]
    
    numero_recepcion = models.CharField(max_length=20, unique=True, blank=True, verbose_name="Nro. Recepción")
    proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Proveedor")
    fecha_recepcion = models.DateField(auto_now_add=True, verbose_name="Fecha de Recepción")
    orden_asociada = models.CharField(max_length=100, blank=True, verbose_name="N° Orden Asociada")
    ubicacion_almacen = models.CharField(max_length=255, blank=True, verbose_name="Ubicación dentro del Almacén")
    estado_mercancia = models.CharField(max_length=255, blank=True, verbose_name="Estado de la Mercancía")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")
    nombre_conductor = models.CharField(max_length=255, blank=True, verbose_name="Nombre del Conductor")
    ci_conductor = models.CharField(max_length=20, blank=True, verbose_name="C.I. Conductor")
    tipo_vehiculo = models.CharField(max_length=100, blank=True, verbose_name="Tipo de Vehículo")
    color_vehiculo = models.CharField(max_length=50, blank=True, verbose_name="Color del Vehículo")
    placa_vehiculo = models.CharField(max_length=20, blank=True, verbose_name="Placa del Vehículo")
    estado = models.CharField(max_length=20, choices=ESTADO_ACTA_CHOICES, default='pendiente', verbose_name="Estado del Acta")

    def save(self, *args, **kwargs):
        if not self.numero_recepcion:
            last_recepcion = ActaRecepcion.objects.all().order_by('-id').first()
            self.numero_recepcion = generar_numero_secuencial('R', last_recepcion, 'numero_recepcion')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Acta de Recepción {self.numero_recepcion} - {self.proveedor.nombre if self.proveedor else 'N/A'}"

    class Meta:
        verbose_name = "Acta de Recepción"
        verbose_name_plural = "Actas de Recepción"

# Modelo: DetalleActaRecepcion
class DetalleActaRecepcion(models.Model):
    acta_recepcion = models.ForeignKey(ActaRecepcion, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Producto")
    nombre_producto_recepcion = models.CharField(max_length=200, blank=True, verbose_name="Nombre del Producto (Recepción)")
    marca = models.CharField(max_length=100, blank=True, verbose_name="Marca")
    modelo = models.CharField(max_length=100, blank=True, verbose_name="Modelo")
    cantidad = models.PositiveIntegerField(verbose_name="Cantidad")

    def save(self, *args, **kwargs):
        if not self.nombre_producto_recepcion and self.producto:
            self.nombre_producto_recepcion = self.producto.nombre
        if not self.marca and self.producto:
            self.marca = self.producto.marca
        if not self.modelo and self.producto:
            self.modelo = self.producto.modelo
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.cantidad} x {self.nombre_producto_recepcion} ({self.acta_recepcion.numero_recepcion})"

    class Meta:
        verbose_name = "Detalle de Acta de Recepción"
        verbose_name_plural = "Detalles de Actas de Recepción"

# Modelo: Cliente
class Cliente(models.Model):
    nombre = models.CharField(max_length=255, verbose_name="Nombre del Cliente")
    cedula_rif = models.CharField(max_length=20, unique=True, blank=True, null=True, verbose_name="Cédula/R.I.F.")
    direccion = models.TextField(blank=True, verbose_name="Dirección")
    telefono = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    email = models.EmailField(blank=True, verbose_name="Email")

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

# Modelo: Cotizacion
class Cotizacion(models.Model):
    ESTADO_COTIZACION_CHOICES = [
        ('abierta', 'Abierta'),
        ('aceptada', 'Aceptada'),
        ('rechazada', 'Rechazada'),
        ('cerrada', 'Cerrada (Completada)'),
        ('en_despacho', 'En Despacho Parcial'),
    ]
    
    numero_cotizacion = models.CharField(max_length=20, unique=True, blank=True, verbose_name="Nro. Cotización")
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='cotizaciones')
    fecha_creacion = models.DateField(auto_now_add=True, verbose_name="Fecha de Creación")
    fecha_validez = models.DateField(blank=True, null=True, verbose_name="Fecha de Validez")
    estado = models.CharField(max_length=20, choices=ESTADO_COTIZACION_CHOICES, default='abierta', verbose_name="Estado")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")
    total_cotizado = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Total Cotizado")

    def clean(self):
        if self.fecha_validez and self.fecha_validez < timezone.now().date():
            raise ValidationError("La fecha de validez no puede ser en el pasado")

    def save(self, *args, **kwargs):
        estado_anterior = None
        if self.pk:
            estado_anterior = Cotizacion.objects.get(pk=self.pk).estado

        if not self.numero_cotizacion:
            last_cotizacion = Cotizacion.objects.all().order_by('-id').first()
            self.numero_cotizacion = generar_numero_secuencial('C', last_cotizacion, 'numero_cotizacion')
        
        super().save(*args, **kwargs)

        if estado_anterior != self.estado and self.estado in ['aceptada', 'en_despacho']:
            self.descontar_stock()

    def descontar_stock(self):
        for detalle in self.detalles.select_related('producto'):
            producto = detalle.producto
            if producto:
                if producto.cantidad < detalle.cantidad:
                    raise ValidationError(f"Stock insuficiente para el producto {producto.nombre}")
                producto.cantidad -= detalle.cantidad
                producto.save()

    def porcentaje_entregado(self):
        detalles = self.detalles.all()
        total_cantidad = sum(d.cantidad for d in detalles)
        entregado = sum(d.cantidad_entregada for d in detalles)
        return (entregado / total_cantidad * 100) if total_cantidad else 0
    
    def productos_pendientes(self):
        """Devuelve los detalles de cotización con cantidades pendientes por entregar"""
        return self.detalles.filter(
            models.Q(cantidad_entregada__lt=models.F('cantidad')) | 
            models.Q(cantidad_entregada=0)
        ).select_related('producto')

    def __str__(self):
        return f"Cotización {self.numero_cotizacion} - {self.cliente.nombre}"

    class Meta:
        verbose_name = "Cotización"
        verbose_name_plural = "Cotizaciones"
        ordering = ['-fecha_creacion']


# Modelo: DetalleCotizacion
class DetalleCotizacion(models.Model):
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Producto")
    nombre_producto_cotizado = models.CharField(max_length=200, blank=True, verbose_name="Nombre del Producto Cotizado")
    marca = models.CharField(max_length=100, blank=True, verbose_name="Marca")
    modelo = models.CharField(max_length=100, blank=True, verbose_name="Modelo")
    cantidad = models.PositiveIntegerField(verbose_name="Cantidad Cotizada")
    cantidad_entregada = models.PositiveIntegerField(default=0, verbose_name="Cantidad Entregada")
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio Unitario")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Subtotal")

    def save(self, *args, **kwargs):
        if self.producto:
            if not self.nombre_producto_cotizado:
                self.nombre_producto_cotizado = self.producto.nombre
            if not self.marca:
                self.marca = self.producto.marca
            if not self.modelo:
                self.modelo = self.producto.modelo
            if not self.precio_unitario:
                self.precio_unitario = self.producto.precio
        if self.cantidad and self.precio_unitario:
            self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.cantidad} x {self.nombre_producto_cotizado} en Cotización {self.cotizacion.numero_cotizacion}"

    class Meta:
        verbose_name = "Detalle de Cotización"
        verbose_name_plural = "Detalles de Cotizaciones"


# Modelo: PagoProveedor
class PagoProveedor(models.Model):
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, related_name='pagos')
    monto = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Monto del Pago")
    fecha_pago = models.DateField(default=timezone.now, verbose_name="Fecha de Pago")
    descripcion = models.TextField(blank=True, verbose_name="Descripción del Pago")

    def __str__(self):
        return f"Pago de ${self.monto} a {self.proveedor.nombre} el {self.fecha_pago}"

    class Meta:
        verbose_name = "Pago a Proveedor"
        verbose_name_plural = "Pagos a Proveedores"
        ordering = ['-fecha_pago']

# Señales
@receiver(post_save, sender=DetalleCotizacion)
@receiver(post_delete, sender=DetalleCotizacion)
def actualizar_total_cotizacion(sender, instance, **kwargs):
    cotizacion = instance.cotizacion
    cotizacion.total_cotizado = sum(
        detalle.subtotal for detalle in cotizacion.detalles.all()
    )
    cotizacion.save(update_fields=['total_cotizado'])

@receiver(post_save, sender=DetalleCotizacion)
def actualizar_estado_cotizacion(sender, instance, **kwargs):
    cotizacion = instance.cotizacion
    if cotizacion.estado in ['abierta', 'aceptada', 'en_despacho']:
        porcentaje = cotizacion.porcentaje_entregado()
        if porcentaje >= 100:
            cotizacion.estado = 'cerrada'
        elif porcentaje > 0:
            cotizacion.estado = 'en_despacho'
        cotizacion.save()

@receiver(post_save, sender=OrdenSalida)
def create_nota_despacho_from_order(sender, instance, created, **kwargs):
    try:
        cliente_nombre = instance.cliente  # ← esto es un string
        cliente_obj = Cliente.objects.get(nombre=cliente_nombre)
    except Cliente.DoesNotExist:
        raise ValueError(f"No se encontró un cliente con nombre '{cliente_nombre}'")

    if created and not instance.nota_despacho_asociada:
        with transaction.atomic():
            # 1. Crear la NotaDespacho
            nota_despacho = NotaDespacho.objects.create(
                cliente=cliente_obj,
                orden_salida_referencia=instance
            )
            instance.nota_despacho_asociada = nota_despacho
            instance.save(update_fields=['nota_despacho_asociada'])

            # 2. Si viene de cotización, agregar productos pendientes
            if instance.cotizacion_origen:
                for detalle_cot in instance.cotizacion_origen.detalles.all():
                    cantidad_pendiente = detalle_cot.cantidad - detalle_cot.cantidad_entregada
                    if cantidad_pendiente > 0 and detalle_cot.producto:
                        DetalleNotaDespacho.objects.create(
                            nota_despacho=nota_despacho,
                            producto=detalle_cot.producto,
                            nombre_producto_despacho=detalle_cot.nombre_producto_cotizado,
                            marca=detalle_cot.marca,
                            modelo=detalle_cot.modelo,
                            cantidad=cantidad_pendiente,
                            detalle_cotizacion_origen=detalle_cot
                        )
            # 3. Si no viene de cotización, agregar productos de la orden
            else:
                for detalle_orden in instance.detalles_orden.all():
                    DetalleNotaDespacho.objects.create(
                        nota_despacho=nota_despacho,
                        producto=detalle_orden.producto,
                        nombre_producto_despacho=detalle_orden.producto.nombre if detalle_orden.producto else '',
                        marca=detalle_orden.producto.marca if detalle_orden.producto else '',
                        modelo=detalle_orden.producto.modelo if detalle_orden.producto else '',
                        cantidad=detalle_orden.cantidad,
                        detalle_cotizacion_origen=None
                    )
@receiver(post_save, sender=DetalleNotaDespacho)
def update_stock_on_detalle_nota_despacho_save(sender, instance, created, **kwargs):
    if instance.producto:
        original_quantity = 0
        if not created:
            try:
                original_instance = sender.objects.get(pk=instance.pk)
                original_quantity = original_instance.cantidad # Usa .cantidad
            except sender.DoesNotExist:
                pass

        quantity_change = instance.cantidad - original_quantity

        # Verificar si viene de cotización y hay suficiente cantidad pendiente
        if instance.detalle_cotizacion_origen:
            # La cantidad_entregada ya incluye lo que ya se entregó de esta cotización.
            # Para validar, necesitamos saber cuánto *queda* por entregar de la cantidad total de la cotización.
            # max_permitido es la cantidad máxima que se puede despachar ADICIONALMENTE a lo que ya se ha entregado.
            max_permitido = instance.detalle_cotizacion_origen.cantidad - instance.detalle_cotizacion_origen.cantidad_entregada

            # Si la cantidad que se está intentando despachar excede lo permitido
            # (es decir, la cantidad actual del detalle de despacho más lo que ya se entregó
            # supera la cantidad total cotizada para ese producto)
            if instance.cantidad > (instance.detalle_cotizacion_origen.cantidad - (instance.detalle_cotizacion_origen.cantidad_entregada - original_quantity)):
                # Si la cantidad actual del detalle de despacho es mayor que la cantidad pendiente
                # (considerando la cantidad original de este detalle)
                # Esto es una validación para evitar que se despache más de lo cotizado.
                # La validación de stock real se hace en el formulario/vista.
                # Aquí, si se intenta despachar más de lo permitido por la cotización,
                # se podría lanzar un error o ajustar la cantidad.
                # Por ahora, dejaremos que el formset maneje la validación.
                pass # La validación de la cantidad se hará en el formset/form.

        # Actualizar stock del producto
        # Esta lógica de stock debe ser muy cuidadosa con los cambios de cantidad.
        # Si 'created' es True, significa que es un nuevo detalle, entonces solo resta la cantidad.
        # Si 'created' es False, significa que se actualizó, entonces resta la diferencia.
        if created:
            instance.producto.cantidad -= instance.cantidad
        else:
            instance.producto.cantidad -= quantity_change

        if instance.producto.cantidad < 0:
            instance.producto.cantidad = 0 # Evitar stock negativo, aunque la validación del formset debería prevenir esto
        instance.producto.save()

        # Crear movimiento
        # Solo crear movimiento si hubo un cambio real de cantidad
        if quantity_change != 0 or created:
            Movimiento.objects.create(
                producto=instance.producto,
                tipo='salida',
                cantidad=abs(quantity_change) if not created else instance.cantidad, # Si es nuevo, la cantidad es la cantidad del detalle
                descripcion=f"Despacho de {instance.cantidad} unidades de {instance.producto.nombre} (Nota Despacho #{instance.nota_despacho.numero_despacho})",
                fecha=timezone.now(),
                guia_salida=None # Asumiendo que la GuiaSalida se asocia en otro proceso si es necesario
            )

        # Actualizar cantidad entregada en cotización si aplica
        if instance.detalle_cotizacion_origen:
            instance.detalle_cotizacion_origen.cantidad_entregada += quantity_change
            instance.detalle_cotizacion_origen.save()

@receiver(post_delete, sender=DetalleNotaDespacho)
def revert_stock_on_detalle_nota_despacho_delete(sender, instance, **kwargs):
    if instance.producto:
        instance.producto.cantidad += instance.cantidad # Usa .cantidad
        instance.producto.save(update_fields=['cantidad'])

        Movimiento.objects.create(
            producto=instance.producto,
            tipo='entrada',
            cantidad=instance.cantidad, # Usa .cantidad
            descripcion=f"Reversión de despacho de {instance.cantidad} unidades de {instance.producto.nombre} (eliminación de Detalle Nota Despacho #{instance.pk} de Nota #{instance.nota_despacho.numero_despacho})",
            fecha=timezone.now(),
            guia_salida=None
        )
        
        if instance.detalle_cotizacion_origen:
            dco = instance.detalle_cotizacion_origen
            dco.cantidad_entregada -= instance.cantidad # Usa .cantidad
            dco.save(update_fields=['cantidad_entregada'])

@receiver(post_save, sender=DetalleActaRecepcion)
def update_product_stock_and_acta_status_on_recepcion_save(sender, instance, created, **kwargs):
    if instance.producto:
        original_quantity = 0
        if not created:
            try:
                original_instance = sender.objects.get(pk=instance.pk)
                original_quantity = original_instance.cantidad
            except sender.DoesNotExist:
                pass

        quantity_change = instance.cantidad - original_quantity

        if created:
            instance.producto.cantidad += instance.cantidad
        else:
            instance.producto.cantidad += quantity_change
        instance.producto.save(update_fields=['cantidad'])

        if quantity_change != 0 or created:
            Movimiento.objects.create(
                producto=instance.producto,
                tipo='entrada',
                cantidad=abs(quantity_change) if not created else instance.cantidad,
                descripcion=f"Recepción de {instance.cantidad} unidades de {instance.producto.nombre} vía Acta de Recepción #{instance.acta_recepcion.numero_recepcion}",
                fecha=timezone.now(),
                acta_recepcion=instance.acta_recepcion
            )
    
    acta = instance.acta_recepcion
    # Recalcular el estado del acta basado en si tiene detalles
    if acta.detalles.exists():
        acta.estado = 'completa' # O podrías tener lógica más compleja para 'parcial'
    else:
        acta.estado = 'pendiente'
    acta.save(update_fields=['estado'])

@receiver(post_delete, sender=DetalleActaRecepcion)
def update_product_stock_and_acta_status_on_recepcion_delete(sender, instance, **kwargs):
    if instance.producto:
        instance.producto.cantidad -= instance.cantidad
        instance.producto.save(update_fields=['cantidad'])

        Movimiento.objects.create(
            producto=instance.producto,
            tipo='salida',
            cantidad=instance.cantidad,
            descripcion=f"Reversión de recepción de {instance.cantidad} unidades de {instance.producto.nombre} (eliminación de Detalle Acta Recepción #{instance.pk} de Acta #{instance.acta_recepcion.numero_recepcion})",
            fecha=timezone.now(),
            acta_recepcion=instance.acta_recepcion
        )
    
    acta = instance.acta_recepcion
    # Recalcular el estado del acta basado en si tiene detalles
    if acta.detalles.exists():
        acta.estado = 'completa'
    else:
        acta.estado = 'pendiente' # If no details left, revert to pending
    acta.save(update_fields=['estado'])

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre
