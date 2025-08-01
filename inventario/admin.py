# inventario/admin.py

from django.contrib import admin
from .models import Producto, Movimiento, GuiaSalida, Almacen, Proveedor, UnidadMedida, NotaDespacho, DetalleNotaDespacho, OrdenSalida, DetalleOrdenSalida, ActaRecepcion, DetalleActaRecepcion, Cliente, Cotizacion, DetalleCotizacion, PagoProveedor

# Inline para DetalleNotaDespacho en NotaDespachoAdmin
class DetalleNotaDespachoInline(admin.TabularInline):
    model = DetalleNotaDespacho
    extra = 1 # Número de formularios vacíos a mostrar
    raw_id_fields = ('producto', 'detalle_cotizacion_origen') # Añadido detalle_cotizacion_origen

class NotaDespachoAdmin(admin.ModelAdmin):
    list_display = ('numero_despacho', 'cliente', 'fecha_despacho', 'proveedor', 'orden_asociada', 'orden_salida_referencia') # Added orden_salida_referencia
    search_fields = ('numero_despacho', 'cliente', 'orden_asociada', 'orden_salida_referencia__id') # Added search for orden_salida_referencia
    list_filter = ('fecha_despacho', 'proveedor')
    inlines = [DetalleNotaDespachoInline] # Añade el inline aquí
    raw_id_fields = ('proveedor', 'orden_salida_referencia') # Added orden_salida_referencia

class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'sku', 'cantidad', 'stock_minimo', 'precio', 'unidad_medida', 'almacen', 'proveedor', 'marca', 'modelo', 'fecha_actualizacion') # Añadidos nuevos campos
    search_fields = ('nombre', 'sku', 'proveedor__nombre', 'almacen__nombre', 'marca', 'modelo') # Búsqueda en campos relacionados
    list_filter = ('fecha_creacion', 'fecha_actualizacion', 'almacen', 'proveedor', 'unidad_medida', 'marca', 'modelo') # Filtros para nuevos campos
    raw_id_fields = ('proveedor', 'almacen', 'unidad_medida') # Para mejorar la UX con muchos elementos

class MovimientoAdmin(admin.ModelAdmin):
    list_display = ('producto', 'tipo', 'cantidad', 'fecha', 'guia_salida', 'acta_recepcion') # Added acta_recepcion
    list_filter = ('tipo', 'fecha', 'producto')
    search_fields = ('producto__nombre', 'descripcion')
    raw_id_fields = ('producto', 'guia_salida', 'acta_recepcion') # Added acta_recepcion

class GuiaSalidaAdmin(admin.ModelAdmin):
    list_display = ('destinatario', 'fecha_creacion', 'nota_despacho', 'acta_recepcion', 'qr_code')
    search_fields = ('destinatario', 'nota_despacho__numero_despacho', 'acta_recepcion__numero_recepcion')
    list_filter = ('fecha_creacion',)
    readonly_fields = ('qr_code',)
    raw_id_fields = ('nota_despacho', 'acta_recepcion')

# Inline para DetalleOrdenSalida en OrdenSalidaAdmin
class DetalleOrdenSalidaInline(admin.TabularInline):
    model = DetalleOrdenSalida
    extra = 1
    raw_id_fields = ('producto',) # Para mejorar la UX con muchos elementos

class OrdenSalidaAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha_orden', 'cliente', 'total', 'nota_despacho_asociada', 'cotizacion_origen') # Added cotizacion_origen
    list_filter = ('fecha_orden',)
    search_fields = ('cliente',)
    inlines = [DetalleOrdenSalidaInline]
    readonly_fields = ('total', 'nota_despacho_asociada') # El total se calcula automáticamente
    raw_id_fields = ('cotizacion_origen',) # Added cotizacion_origen

# Inline para DetalleActaRecepcion en ActaRecepcionAdmin
class DetalleActaRecepcionInline(admin.TabularInline):
    model = DetalleActaRecepcion
    extra = 1
    raw_id_fields = ('producto',)

class ActaRecepcionAdmin(admin.ModelAdmin):
    list_display = ('numero_recepcion', 'proveedor', 'fecha_recepcion', 'orden_asociada', 'ubicacion_almacen', 'estado') # Added 'estado'
    search_fields = ('numero_recepcion', 'proveedor__nombre', 'orden_asociada')
    list_filter = ('fecha_recepcion', 'proveedor', 'estado') # Added 'estado'
    inlines = [DetalleActaRecepcionInline]
    raw_id_fields = ('proveedor',)

class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'cedula_rif', 'telefono', 'email')
    search_fields = ('nombre', 'cedula_rif', 'telefono', 'email')

# Inline para DetalleCotizacion en CotizacionAdmin
class DetalleCotizacionInline(admin.TabularInline):
    model = DetalleCotizacion
    extra = 1
    raw_id_fields = ('producto',)

class CotizacionAdmin(admin.ModelAdmin):
    list_display = ('numero_cotizacion', 'cliente', 'fecha_creacion', 'fecha_validez', 'estado', 'total_cotizado')
    search_fields = ('numero_cotizacion', 'cliente__nombre')
    list_filter = ('fecha_creacion', 'estado')
    inlines = [DetalleCotizacionInline]
    raw_id_fields = ('cliente',)
    readonly_fields = ('total_cotizado',) # Total se calcula automáticamente

class PagoProveedorAdmin(admin.ModelAdmin): # New Admin for PagoProveedor
    list_display = ('proveedor', 'monto', 'fecha_pago', 'descripcion')
    list_filter = ('fecha_pago', 'proveedor')
    search_fields = ('proveedor__nombre', 'descripcion')
    raw_id_fields = ('proveedor',)


# Registra los nuevos modelos en el administrador
admin.site.register(Almacen)
admin.site.register(Proveedor)
admin.site.register(UnidadMedida)

admin.site.register(Producto, ProductoAdmin)
admin.site.register(Movimiento, MovimientoAdmin)
admin.site.register(GuiaSalida, GuiaSalidaAdmin)
admin.site.register(NotaDespacho, NotaDespachoAdmin)
admin.site.register(OrdenSalida, OrdenSalidaAdmin)
admin.site.register(ActaRecepcion, ActaRecepcionAdmin)
admin.site.register(Cliente, ClienteAdmin)
admin.site.register(Cotizacion, CotizacionAdmin)
admin.site.register(PagoProveedor, PagoProveedorAdmin) # Register PagoProveedor