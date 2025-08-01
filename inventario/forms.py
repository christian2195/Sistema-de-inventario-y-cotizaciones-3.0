# inventario/forms.py
from django import forms
from django.core.exceptions import ValidationError
from .models import (
    GuiaSalida, Producto, Categoria, UnidadMedida, Proveedor, Almacen,
    TipoMovimiento, Cliente, Movimiento, DetalleMovimiento, NotaDespacho,
    DetalleNotaDespacho, OrdenSalida
)

class NotaDespachoForm(forms.ModelForm):
    class Meta:
        model = NotaDespacho
        fields = [
            'numero_despacho', 'cliente', 'almacen_origen', 'tipo_despacho',
            'fecha_despacho', 'proveedor', 'orden_asociada', 'observaciones',
            'nombre_receptor_despacho', 'ci_receptor_despacho',
            'nombre_conductor', 'ci_conductor', 'tipo_vehiculo',
            'color_vehiculo', 'placa_vehiculo', 'orden_salida_referencia'
        ]
        widgets = {
            'numero_despacho': forms.TextInput(attrs={'class': 'block w-full p-2 rounded-md border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50', 'readonly': 'readonly'}),
            'cliente': forms.Select(attrs={'class': 'block w-full p-2 rounded-md border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50'}),
            'almacen_origen': forms.Select(attrs={'class': 'block w-full p-2 rounded-md border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50'}),
            'tipo_despacho': forms.Select(attrs={'class': 'block w-full p-2 rounded-md border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50'}),
            'fecha_despacho': forms.DateInput(attrs={'class': 'block w-full p-2 rounded-md border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50', 'type': 'date', 'readonly': 'readonly'}),
            'proveedor': forms.Select(attrs={'class': 'block w-full p-2 rounded-md border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50'}),
            'orden_asociada': forms.TextInput(attrs={'class': 'block w-full p-2 rounded-md border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50'}),
            'observaciones': forms.Textarea(attrs={'rows': 3, 'class': 'block w-full p-2 rounded-md border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50'}),
            'nombre_receptor_despacho': forms.TextInput(attrs={'class': 'block w-full p-2 rounded-md border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50'}),
            'ci_receptor_despacho': forms.TextInput(attrs={'class': 'block w-full p-2 rounded-md border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50'}),
            'nombre_conductor': forms.TextInput(attrs={'class': 'block w-full p-2 rounded-md border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50'}),
            'ci_conductor': forms.TextInput(attrs={'class': 'block w-full p-2 rounded-md border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50'}),
            'tipo_vehiculo': forms.TextInput(attrs={'class': 'block w-full p-2 rounded-md border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50'}),
            'color_vehiculo': forms.TextInput(attrs={'class': 'block w-full p-2 rounded-md border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50'}),
            'placa_vehiculo': forms.TextInput(attrs={'class': 'block w-full p-2 rounded-md border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50'}),
            'orden_salida_referencia': forms.Select(attrs={'class': 'block w-full p-2 rounded-md border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50'}),
        }

class DetalleNotaDespachoForm(forms.ModelForm):
    class Meta:
        model = DetalleNotaDespacho
        fields = ['id', 'producto', 'nombre_producto_despacho', 'marca', 'modelo', 'cantidad', 'detalle_cotizacion_origen']
        widgets = {
            'producto': forms.HiddenInput(),
            'nombre_producto_despacho': forms.HiddenInput(),
            'marca': forms.HiddenInput(),
            'modelo': forms.HiddenInput(),
            'cantidad': forms.HiddenInput(),
            'detalle_cotizacion_origen': forms.HiddenInput(),
        }

    def clean_cantidad(self):
        cantidad = self.cleaned_data['cantidad']
        producto = self.cleaned_data.get('producto')

        # Solo validar stock si no se está eliminando el detalle
        if producto and not self.cleaned_data.get('DELETE'):
            original_cantidad_detalle = 0
            if self.instance.pk:
                original_cantidad_detalle = self.instance.cantidad

            effective_stock = producto.cantidad + original_cantidad_detalle

            if cantidad > effective_stock:
                raise ValidationError(
                    f"No hay suficiente stock para despachar {cantidad} unidades de {producto.nombre}. "
                    f"Stock disponible: {effective_stock}."
                )
        return cantidad

from django.forms import inlineformset_factory

DetalleNotaDespachoFormSet = inlineformset_factory(
    NotaDespacho,
    DetalleNotaDespacho,
    form=DetalleNotaDespachoForm,
    extra=1,
    can_delete=True
)

class MovimientoForm(forms.ModelForm):
    cantidad_producto = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        label="Cantidad"
    )

    class Meta:
        model = Movimiento
        fields = ['tipo_movimiento', 'observaciones']
        widgets = {
            'tipo_movimiento': forms.Select(attrs={'class': 'form-control'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'tipo_movimiento': 'Tipo de Movimiento',
            'observaciones': 'Observaciones/Motivo',
        }