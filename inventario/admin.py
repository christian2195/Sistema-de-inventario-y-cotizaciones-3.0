# inventario/admin.py

from django.contrib import admin
from .models import (
    Almacen, Proveedor, UnidadMedida, Producto, Movimiento,
    GuiaSalida, NotaDespacho, DetalleNotaDespacho, OrdenSalida,
    DetalleOrdenSalida, ActaRecepcion, DetalleActaRecepcion,
    Cliente, Cotizacion, DetalleCotizacion, PagoProveedor,
    TipoMovimiento, Categoria # Importa TipoMovimiento y Categoria
)

# Registra tus modelos aquí.

@admin.register(Almacen)
class AlmacenAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'ubicacion')
    search_fields = ('nombre',)

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'contacto', 'telefono', 'email')
    search_fields = ('nombre', 'email')

@admin.register(UnidadMedida)
class UnidadMedidaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'abreviatura')
    search_fields = ('nombre', 'abreviatura')

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'sku', 'cantidad', 'precio', 'almacen', 'stock_minimo', 'necesita_reabastecimiento')
    list_filter = ('almacen', 'proveedor', 'unidad_medida', 'marca')
    search_fields = ('nombre', 'sku', 'descripcion', 'marca', 'modelo')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')

    def necesita_reabastecimiento(self, obj):
        return obj.necesita_reabastecimiento()
    necesita_reabastecimiento.boolean = True
    necesita_reabastecimiento.short_description = 'Necesita Reabastecimiento'

@admin.register(TipoMovimiento)
class TipoMovimientoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'es_entrada', 'es_salida', 'es_traslado')
    search_fields = ('nombre',)
    list_filter = ('es_entrada', 'es_salida', 'es_traslado')

@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    # CAMBIO: 'tipo' ha sido reemplazado por 'tipo_movimiento__nombre' para mostrar el nombre
    # Añadidos 'almacen_origen', 'almacen_destino', 'responsable'
    list_display = ('producto', 'tipo_movimiento', 'cantidad', 'fecha', 'descripcion', 'almacen_origen', 'almacen_destino', 'responsable')
    # CAMBIO: 'tipo' ha sido reemplazado por 'tipo_movimiento' para el filtro
    list_filter = ('tipo_movimiento', 'fecha', 'almacen_origen', 'almacen_destino', 'responsable')
    search_fields = ('producto__nombre', 'descripcion', 'tipo_movimiento__nombre', 'almacen_origen__nombre', 'almacen_destino__nombre', 'responsable__username') # Updated search fields
    readonly_fields = ('fecha',) # La fecha se establece automáticamente

    def tipo_movimiento(self, obj):
        return obj.tipo_movimiento.nombre
    tipo_movimiento.short_description = 'Tipo de Movimiento'


@admin.register(GuiaSalida)
class GuiaSalidaAdmin(admin.ModelAdmin):
    list_display = ('fecha_creacion', 'destinatario', 'nota_despacho', 'acta_recepcion')
    list_filter = ('fecha_creacion',)
    search_fields = ('destinatario', 'nota_despacho__numero_despacho')
    readonly_fields = ('qr_code',) # QR code is generated automatically

class DetalleNotaDespachoInline(admin.TabularInline):
    model = DetalleNotaDespacho
    extra = 1
    # Added detalle_cotizacion_origen
    fields = ('producto', 'cantidad', 'nombre_producto_despacho', 'marca', 'modelo', 'detalle_cotizacion_origen')
    autocomplete_fields = ['producto'] # Enable autocomplete for product selection

@admin.register(NotaDespacho)
class NotaDespachoAdmin(admin.ModelAdmin):
    list_display = ('numero_despacho', 'cliente', 'fecha_despacho', 'orden_asociada', 'creado_por')
    list_filter = ('fecha_despacho', 'cliente', 'creado_por')
    search_fields = ('numero_despacho', 'cliente__nombre', 'orden_asociada', 'nombre_conductor')
    inlines = [DetalleNotaDespachoInline]
    readonly_fields = ('numero_despacho',) # Numero de despacho is generated automatically

    def save_model(self, request, obj, form, change):
        if not obj.pk: # Only set creado_por on creation
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)

class DetalleOrdenSalidaInline(admin.TabularInline):
    model = DetalleOrdenSalida
    extra = 1
    autocomplete_fields = ['producto']

@admin.register(OrdenSalida)
class OrdenSalidaAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha_orden', 'cliente', 'total', 'cotizacion_origen')
    list_filter = ('fecha_orden',)
    search_fields = ('cliente', 'id')
    inlines = [DetalleOrdenSalidaInline]
    readonly_fields = ('total',) # Total is calculated automatically

class DetalleActaRecepcionInline(admin.TabularInline):
    model = DetalleActaRecepcion
    extra = 1
    autocomplete_fields = ['producto']

@admin.register(ActaRecepcion)
class ActaRecepcionAdmin(admin.ModelAdmin):
    list_display = ('numero_recepcion', 'proveedor', 'fecha_recepcion', 'estado', 'orden_asociada')
    list_filter = ('fecha_recepcion', 'proveedor', 'estado')
    search_fields = ('numero_recepcion', 'proveedor__nombre', 'orden_asociada')
    inlines = [DetalleActaRecepcionInline]
    raw_id_fields = ('proveedor',)

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'cedula_rif', 'telefono', 'email')
    search_fields = ('nombre', 'cedula_rif', 'telefono', 'email')

class DetalleCotizacionInline(admin.TabularInline):
    model = DetalleCotizacion
    extra = 1
    autocomplete_fields = ['producto']

@admin.register(Cotizacion)
class CotizacionAdmin(admin.ModelAdmin):
    list_display = ('numero_cotizacion', 'cliente', 'fecha_creacion', 'fecha_validez', 'estado', 'total_cotizado')
    list_filter = ('estado', 'fecha_creacion', 'fecha_validez')
    search_fields = ('numero_cotizacion', 'cliente__nombre')
    inlines = [DetalleCotizacionInline]
    readonly_fields = ('numero_cotizacion', 'total_cotizado')

@admin.register(PagoProveedor)
class PagoProveedorAdmin(admin.ModelAdmin):
    list_display = ('proveedor', 'monto', 'fecha_pago', 'descripcion')
    list_filter = ('proveedor', 'fecha_pago')
    search_fields = ('proveedor__nombre', 'descripcion')

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha_creacion', 'fecha_actualizacion')
    search_fields = ('nombre',)

# Registra los modelos restantes en el administrador
# Se eliminaron todas las líneas duplicadas que usaban admin.site.register()
# para modelos que ya están registrados con el decorador @admin.register.
# Esto incluye Almacen, Proveedor, UnidadMedida, Producto, Movimiento,
# GuiaSalida, NotaDespacho, OrdenSalida, ActaRecepcion, Cliente, Cotizacion,
# PagoProveedor, y Categoria.