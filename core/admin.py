from django.contrib import admin
from .models import (
    Proveedor, Cliente, Almacen, Producto, ActaRecepcion, 
    MovimientoInventario, Cotizacion, ItemCotizacion, 
    NotaDespacho, ItemDespacho, PagoProveedor
)

# Proyecto: EMVEPRO
# Autor: Gerencia de Tecnología de la Información y Comunicación

# --- Inlines para mejorar la carga de datos ---

class ItemCotizacionInline(admin.TabularInline):
    model = ItemCotizacion
    extra = 1

class ItemDespachoInline(admin.TabularInline):
    model = ItemDespacho
    extra = 1

# --- Registros de Modelos ---

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rif_nit', 'contacto_principal', 'telefono')
    search_fields = ('nombre', 'rif_nit')

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rif_nit', 'contacto_principal', 'telefono')
    search_fields = ('nombre', 'rif_nit')

@admin.register(Almacen)
class AlmacenAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'ubicacion', 'activo')
    list_filter = ('activo',)

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('codigo_sku', 'nombre', 'stock_actual', 'activo')
    search_fields = ('codigo_sku', 'nombre')
    list_filter = ('activo',)
    readonly_fields = ('stock_actual',) 

@admin.register(ActaRecepcion)
class ActaRecepcionAdmin(admin.ModelAdmin):
    list_display = ('id', 'proveedor', 'almacen', 'numero_factura_proveedor', 'monto_total_factura', 'fecha_recepcion', 'responsable')
    list_filter = ('fecha_recepcion', 'almacen', 'proveedor')
    search_fields = ('numero_factura_proveedor', 'proveedor__nombre')

@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = ('producto', 'tipo', 'cantidad', 'almacen', 'fecha_movimiento', 'responsable')
    list_filter = ('tipo', 'fecha_movimiento', 'almacen')
    search_fields = ('producto__nombre', 'producto__codigo_sku')
    readonly_fields = ('fecha_movimiento',)

@admin.register(Cotizacion)
class CotizacionAdmin(admin.ModelAdmin):
    list_display = ('numero_rastreo', 'cliente', 'fecha_emision', 'estatus')
    list_filter = ('estatus', 'fecha_emision')
    search_fields = ('numero_rastreo', 'cliente__nombre')
    readonly_fields = ('numero_rastreo',)
    inlines = [ItemCotizacionInline]

@admin.register(NotaDespacho)
class NotaDespachoAdmin(admin.ModelAdmin):
    list_display = ('numero_guia', 'cotizacion', 'fecha_despacho', 'responsable')
    search_fields = ('numero_guia', 'cotizacion__numero_rastreo')
    list_filter = ('fecha_despacho',)
    inlines = [ItemDespachoInline]

@admin.register(PagoProveedor)
class PagoProveedorAdmin(admin.ModelAdmin):
    list_display = ('proveedor', 'monto_pagado', 'fecha_pago', 'referencia_pago', 'responsable')
    list_filter = ('proveedor', 'fecha_pago')
    search_fields = ('proveedor__nombre', 'referencia_pago')