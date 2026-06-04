from django import forms
from django.forms import inlineformset_factory
from .models import Producto, Cotizacion, ItemCotizacion, ActaRecepcion, MovimientoInventario, NotaDespacho, ItemDespacho

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['codigo_sku', 'nombre', 'descripcion', 'activo']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }

# --- NUEVOS FORMULARIOS PARA EL PILAR 3 ---

class CotizacionForm(forms.ModelForm):
    class Meta:
        model = Cotizacion
        fields = ['cliente', 'observaciones']
        widgets = {
            'observaciones': forms.Textarea(attrs={'rows': 2}),
        }

class ItemCotizacionForm(forms.ModelForm):
    class Meta:
        model = ItemCotizacion
        fields = ['producto', 'cantidad_solicitada', 'precio_unitario']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-select'}),
            'cantidad_solicitada': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

# Esta es la magia: vincula la Cotización (Padre) con sus Ítems (Hijos)
ItemCotizacionFormSet = inlineformset_factory(
    Cotizacion, ItemCotizacion, 
    form=ItemCotizacionForm,
    extra=1, # Muestra 1 fila en blanco por defecto
    can_delete=True
)

# --- FORMULARIOS PARA EL PILAR 1 (RECEPCIÓN DE MERCANCÍA) ---

class ActaRecepcionForm(forms.ModelForm):
    class Meta:
        model = ActaRecepcion
        fields = ['proveedor', 'almacen', 'numero_factura_proveedor', 'monto_total_factura', 'responsable', 'observaciones']
        widgets = {
            'observaciones': forms.Textarea(attrs={'rows': 2}),
            'monto_total_factura': forms.NumberInput(attrs={'step': '0.01'}),
        }

class MovimientoRecepcionForm(forms.ModelForm):
    class Meta:
        model = MovimientoInventario
        # Agregamos costo_unitario a la lista
        fields = ['producto', 'cantidad', 'costo_unitario']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-select'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            # Le damos estilo al nuevo campo
            'costo_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

# Vincula el Acta (Padre) con los Movimientos de Entrada (Hijos)
MovimientoRecepcionFormSet = inlineformset_factory(
    ActaRecepcion, MovimientoInventario, 
    form=MovimientoRecepcionForm,
    extra=1,
    can_delete=True
)

class NotaDespachoForm(forms.ModelForm):
    class Meta:
        model = NotaDespacho
        fields = ['cotizacion', 'numero_guia', 'responsable']
        widgets = {
            'cotizacion': forms.Select(attrs={'class': 'form-select'}),
        }

class ItemDespachoForm(forms.ModelForm):
    class Meta:
        model = ItemDespacho
        fields = ['item_cotizacion', 'cantidad_despachada', 'almacen_origen']
        widgets = {
            'item_cotizacion': forms.Select(attrs={'class': 'form-select'}),
            'cantidad_despachada': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'almacen_origen': forms.Select(attrs={'class': 'form-select'}),
        }

# Vinculamos la Guía de Despacho (Padre) con los Ítems a despachar (Hijos)
ItemDespachoFormSet = inlineformset_factory(
    NotaDespacho, ItemDespacho, 
    form=ItemDespachoForm,
    extra=1,
    can_delete=True
)