from django import forms
from django.forms import inlineformset_factory
from .models import Producto, Cotizacion, ItemCotizacion, NotaDespacho, ItemDespacho, ActaRecepcion, MovimientoInventario

# ==============================================================================
# 1. FORMULARIOS DE PRODUCTOS Y ALMACÉN BASE
# ==============================================================================
class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['codigo_sku', 'nombre', 'descripcion', 'stock_actual', 'costo_compra', 'precio_venta', 'activo']
        widgets = {
            'codigo_sku': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'stock_actual': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'costo_compra': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'precio_venta': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

# ==============================================================================
# 2. PILAR DE COTIZACIONES (MATRIZ DE COSTOS MULTIDIVISA)
# ==============================================================================
class CotizacionForm(forms.ModelForm):
    class Meta:
        model = Cotizacion
        fields = ['cliente', 'referencia_proyecto', 'tasa_bcv', 'observacion_tasa', 'incluye_iva', 'observaciones', 'estatus']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-select select2'}),
            'referencia_proyecto': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: HOSPITAL MILITAR'}),
            'tasa_bcv': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'observacion_tasa': forms.TextInput(attrs={'class': 'form-control'}),
            'incluye_iva': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'estatus': forms.Select(attrs={'class': 'form-select'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class ItemCotizacionForm(forms.ModelForm):
    class Meta:
        model = ItemCotizacion
        fields = ['seccion_departamento', 'producto', 'cantidad_solicitada', 'costo_base_usd', 'factor_margen', 'observacion_item']
        widgets = {
            'seccion_departamento': forms.TextInput(attrs={'class': 'form-control'}),
            'producto': forms.Select(attrs={'class': 'form-select select2'}),
            'cantidad_solicitada': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'costo_base_usd': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'factor_margen': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'observacion_item': forms.TextInput(attrs={'class': 'form-control'}),
        }

ItemCotizacionFormSet = inlineformset_factory(Cotizacion, ItemCotizacion, form=ItemCotizacionForm, extra=1, can_delete=True)


# ==============================================================================
# 3. PILAR DE ENTRADAS (ACTAS DE RECEPCIÓN) - ¡RESTAURADOS!
# ==============================================================================
class ActaRecepcionForm(forms.ModelForm):
    class Meta:
        model = ActaRecepcion
        fields = [
            'proveedor', 'almacen', 'numero_factura_proveedor', 'monto_total_factura',
            'institucion', 'nro_orden_asociada', 'ubicacion_almacen', 'estado_mercancia',
            'nombre_conductor', 'cedula_conductor', 'tipo_vehiculo', 'color_vehiculo', 'placa_vehiculo',
            'beneficiario_autorizado', 'cedula_beneficiario', 'telefono_beneficiario',
            'fecha_hora_llegada_conductor', 'fecha_hora_llegada_beneficiario', 'observaciones'
        ]
        widgets = {
            'proveedor': forms.Select(attrs={'class': 'form-select select2'}),
            'almacen': forms.Select(attrs={'class': 'form-select'}),
            'numero_factura_proveedor': forms.TextInput(attrs={'class': 'form-control'}),
            'monto_total_factura': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'institucion': forms.TextInput(attrs={'class': 'form-control'}),
            'nro_orden_asociada': forms.TextInput(attrs={'class': 'form-control'}),
            'ubicacion_almacen': forms.TextInput(attrs={'class': 'form-control'}),
            'estado_mercancia': forms.Select(attrs={'class': 'form-select'}),
            'nombre_conductor': forms.TextInput(attrs={'class': 'form-control'}),
            'cedula_conductor': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_vehiculo': forms.TextInput(attrs={'class': 'form-control'}),
            'color_vehiculo': forms.TextInput(attrs={'class': 'form-control'}),
            'placa_vehiculo': forms.TextInput(attrs={'class': 'form-control'}),
            'beneficiario_autorizado': forms.TextInput(attrs={'class': 'form-control'}),
            'cedula_beneficiario': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono_beneficiario': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_hora_llegada_conductor': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'fecha_hora_llegada_beneficiario': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class MovimientoRecepcionForm(forms.ModelForm):
    class Meta:
        model = MovimientoInventario
        fields = ['producto', 'cantidad', 'costo_unitario', 'observacion']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-select select2'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'costo_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'observacion': forms.TextInput(attrs={'class': 'form-control'}),
        }

# Fábrica que usa la vista crear_acta_recepcion en la línea 132 de views.py
MovimientoRecepcionFormSet = inlineformset_factory(ActaRecepcion, MovimientoInventario, form=MovimientoRecepcionForm, extra=1, can_delete=True)


# ==============================================================================
# 4. PILAR DE SALIDAS (NOTAS DE DESPACHO CON ALMACÉN POR RENGLÓN)
# ==============================================================================
class NotaDespachoForm(forms.ModelForm):
    class Meta:
        model = NotaDespacho
        fields = [
            'cotizacion', 'numero_guia', 'nombre_beneficiario', 'proveedor_origen', 
            'nro_orden_asociada', 'nombre_conductor', 'cedula_conductor', 
            'tipo_vehiculo', 'color_vehiculo', 'placa_vehiculo', 'beneficiario_autorizado', 
            'cedula_beneficiario', 'telefono_beneficiario', 'fecha_hora_llegada_conductor', 
            'fecha_hora_llegada_beneficiario', 'observaciones'
        ]
        widgets = {
            'cotizacion': forms.Select(attrs={'class': 'form-select select2'}),
            'numero_guia': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: D-0000001'}),
            'nombre_beneficiario': forms.TextInput(attrs={'class': 'form-control'}),
            'proveedor_origen': forms.TextInput(attrs={'class': 'form-control'}),
            'nro_orden_asociada': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_conductor': forms.TextInput(attrs={'class': 'form-control'}),
            'cedula_conductor': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_vehiculo': forms.TextInput(attrs={'class': 'form-control'}),
            'color_vehiculo': forms.TextInput(attrs={'class': 'form-control'}),
            'placa_vehiculo': forms.TextInput(attrs={'class': 'form-control'}),
            'beneficiario_autorizado': forms.TextInput(attrs={'class': 'form-control'}),
            'cedula_beneficiario': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono_beneficiario': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_hora_llegada_conductor': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'fecha_hora_llegada_beneficiario': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class ItemDespachoForm(forms.ModelForm):
    class Meta:
        model = ItemDespacho
        fields = ['item_cotizacion', 'almacen_origen', 'marca', 'modelo', 'cantidad_despachada']
        widgets = {
            'item_cotizacion': forms.Select(attrs={'class': 'form-select'}),
            'almacen_origen': forms.Select(attrs={'class': 'form-select'}),
            'marca': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Marca'}),
            'modelo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Modelo'}),
            'cantidad_despachada': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

ItemDespachoFormSet = inlineformset_factory(NotaDespacho, ItemDespacho, form=ItemDespachoForm, extra=1, can_delete=True)