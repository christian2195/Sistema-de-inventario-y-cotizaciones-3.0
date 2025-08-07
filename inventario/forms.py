# inventario/forms.py
from django import forms
from django.core.exceptions import ValidationError
from .models import (
    GuiaSalida, Producto, Categoria, UnidadMedida, Proveedor, Almacen,
    TipoMovimiento, Cliente, Movimiento, DetalleMovimiento, NotaDespacho,
    DetalleNotaDespacho, OrdenSalida, Cotizacion, DetalleCotizacion # Asegúrate de importar los modelos necesarios
)

class NotaDespachoForm(forms.ModelForm):
    """
    Formulario principal para la Nota de Despacho.
    """
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
            'fecha_despacho': forms.DateInput(attrs={'type': 'date', 'class': 'block w-full p-2 rounded-md border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50'}),
            'proveedor': forms.Select(attrs={'class': 'block w-full p-2 rounded-md border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50'}),
            'orden_asociada': forms.Select(attrs={'class': 'block w-full p-2 rounded-md border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50'}),
            'observaciones': forms.Textarea(attrs={'class': 'block w-full p-2 rounded-md border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50', 'rows': 3}),
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
    """
    Formulario para los detalles de la Nota de Despacho, con validación de stock.
    """
    class Meta:
        model = DetalleNotaDespacho
        fields = ['producto', 'cantidad', 'detalle_cotizacion_origen']
    
    def clean_cantidad(self):
        """
        Valida que la cantidad a despachar no sea mayor que el stock disponible.
        """
        cantidad = self.cleaned_data.get('cantidad')
        producto = self.cleaned_data.get('producto')

        if not isinstance(cantidad, (int, float)) or cantidad <= 0:
            raise ValidationError("La cantidad debe ser un número positivo.")

        # Obtener el stock actual del producto.
        # Para evitar problemas con la edición, si ya existe un detalle,
        # sumamos la cantidad original para validar contra el stock "efectivo".
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