from django import forms
from django.contrib.auth.models import User
from django.forms import inlineformset_factory
from .models import (
    Producto, Cotizacion, ItemCotizacion,
    NotaDespacho, ItemDespacho, ActaRecepcion, MovimientoInventario,
    NotaDevolucion, ItemDevolucion, Cliente, Proveedor, Almacen
)

class UsuarioForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Contraseña",
        required=False,
        help_text="Deje en blanco al editar si no desea cambiar la contraseña actual."
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")
        if password:
            user.set_password(password)  # Encripta la contraseña de forma segura
        if commit:
            user.save()
        return user
        
# ==============================================================================
# FORMULARIOS AUXILIARES DE CREACIÓN RÁPIDA (usados en vistas)
# ==============================================================================
class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'rif_nit', 'telefono', 'email', 'direccion']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'rif_nit': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ['nombre', 'rif_nit', 'telefono', 'email', 'direccion']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'rif_nit': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class AlmacenForm(forms.ModelForm):
    class Meta:
        model = Almacen
        fields = ['nombre', 'ubicacion']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'ubicacion': forms.TextInput(attrs={'class': 'form-control'}),
        }


# ==============================================================================
# 1. FORMULARIOS DE PRODUCTOS
# ==============================================================================
class ProductoForm(forms.ModelForm):
    # 1. Sobrescribimos los campos conflictivos declarándolos estrictamente como Enteros
    stock_actual = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '1'}),
        label="Stock actual*"
    )
    costo_compra = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '1', 'placeholder': '0'}),
        label="Costo de Compra (USD)*",
        required=False
    )
    precio_venta = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '1', 'placeholder': '0'}),
        label="Precio de Venta (USD)*",
        required=False
    )

    class Meta:
        model = Producto
        fields = [
            'codigo_sku', 
            'nombre', 
            'almacen', 
            'costo_compra', 
            'precio_venta', 
            'stock_actual', 
            'imagen', 
            'descripcion', 
            'activo'
        ]
        # 2. Dejamos en widgets solo los que no sobrescribimos arriba
        widgets = {
            'codigo_sku': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Interceptamos los datos de la base de datos al editar y los forzamos a enteros
        if self.instance and self.instance.pk:
            if self.instance.stock_actual is not None:
                self.initial['stock_actual'] = int(self.instance.stock_actual)
                
            if self.instance.costo_compra is not None:
                self.initial['costo_compra'] = int(self.instance.costo_compra)
                
            if self.instance.precio_venta is not None:
                self.initial['precio_venta'] = int(self.instance.precio_venta)


# ==============================================================================
# 2. PILAR DE COTIZACIONES (MATRIZ DE COSTOS MULTIDIVISA)
# ==============================================================================
class CotizacionForm(forms.ModelForm):
    class Meta:
        model = Cotizacion
        # Se mantiene 'estatus' para anulaciones manuales; si no se usa, se puede eliminar.
        fields = ['cliente', 'referencia_proyecto', 'tasa_bcv', 'observacion_tasa',
                  'incluye_iva', 'observaciones', 'estatus', 'formato_pdf']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-select select2'}),
            'referencia_proyecto': forms.TextInput(attrs={'class': 'form-control',
                                                          'placeholder': 'Ej: HOSPITAL MILITAR'}),
            'tasa_bcv': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'observacion_tasa': forms.TextInput(attrs={'class': 'form-control'}),
            'incluye_iva': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'estatus': forms.Select(attrs={'class': 'form-select'}),
            'formato_pdf': forms.Select(attrs={'class': 'form-select'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class ItemCotizacionForm(forms.ModelForm):
    class Meta:
        model = ItemCotizacion
        fields = ['seccion_departamento', 'producto', 'cantidad_solicitada',
                  'costo_base_usd', 'factor_margen', 'observacion_item']
        widgets = {
            'seccion_departamento': forms.TextInput(attrs={'class': 'form-control'}),
            'producto': forms.Select(attrs={'class': 'form-select select2'}),
            'cantidad_solicitada': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'costo_base_usd': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'factor_margen': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'observacion_item': forms.TextInput(attrs={'class': 'form-control'}),
        }


ItemCotizacionFormSet = inlineformset_factory(
    Cotizacion, ItemCotizacion,
    form=ItemCotizacionForm,
    extra=1,
    can_delete=True
)


# ==============================================================================
# 3. PILAR DE ENTRADAS (ACTAS DE RECEPCIÓN)
# ==============================================================================
class ActaRecepcionForm(forms.ModelForm):
    class Meta:
        model = ActaRecepcion
        fields = [
            'proveedor', 'almacen', 'numero_factura_proveedor', 'monto_total_factura',
            'institucion', 'nro_orden_asociada', 'ubicacion_almacen', 'estado_mercancia',
            'nombre_conductor', 'cedula_conductor', 'tipo_vehiculo', 'color_vehiculo',
            'placa_vehiculo', 'beneficiario_autorizado', 'cedula_beneficiario',
            'telefono_beneficiario', 'fecha_hora_llegada_conductor',
            'fecha_hora_llegada_beneficiario', 'observaciones'
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
            'fecha_hora_llegada_conductor': forms.DateTimeInput(attrs={
                'class': 'form-control', 'type': 'datetime-local'
            }),
            'fecha_hora_llegada_beneficiario': forms.DateTimeInput(attrs={
                'class': 'form-control', 'type': 'datetime-local'
            }),
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


MovimientoRecepcionFormSet = inlineformset_factory(
    ActaRecepcion, MovimientoInventario,
    form=MovimientoRecepcionForm,
    extra=1,
    can_delete=True
)


# ==============================================================================
# 4. PILAR DE SALIDAS (NOTAS DE DESPACHO)
# ==============================================================================
class NotaDespachoForm(forms.ModelForm):
    class Meta:
        model = NotaDespacho
        fields = [
            'cotizacion', 'nombre_beneficiario', 'proveedor_origen',
            'nro_orden_asociada', 'nombre_conductor', 'cedula_conductor',
            'tipo_vehiculo', 'color_vehiculo', 'placa_vehiculo',
            'beneficiario_autorizado', 'cedula_beneficiario', 'telefono_beneficiario',
            'fecha_hora_llegada_conductor', 'fecha_hora_llegada_beneficiario',
            'observaciones'
        ]
        widgets = {
            'cotizacion': forms.Select(attrs={'class': 'form-select select2'}),
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
            'fecha_hora_llegada_conductor': forms.DateTimeInput(attrs={
                'class': 'form-control', 'type': 'datetime-local'
            }),
            'fecha_hora_llegada_beneficiario': forms.DateTimeInput(attrs={
                'class': 'form-control', 'type': 'datetime-local'
            }),
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


ItemDespachoFormSet = inlineformset_factory(
    NotaDespacho, ItemDespacho,
    form=ItemDespachoForm,
    extra=1,
    can_delete=True
)


# ==============================================================================
# 5. PILAR DE DEVOLUCIONES (LOGÍSTICA INVERSA A PROVEEDORES)
# ==============================================================================
class NotaDevolucionForm(forms.ModelForm):
    class Meta:
        model = NotaDevolucion
        # Se incluyen todos los campos relevantes para el acto de devolución
        fields = [
            'proveedor', 'origen_devolucion', 'motivo_devolucion',
            'observaciones', 'nombre_conductor', 'cedula_conductor',
            'placa_vehiculo'
        ]
        widgets = {
            'proveedor': forms.Select(attrs={'class': 'form-select select2'}),
            'origen_devolucion': forms.TextInput(attrs={'class': 'form-control'}),
            'motivo_devolucion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'nombre_conductor': forms.TextInput(attrs={'class': 'form-control'}),
            'cedula_conductor': forms.TextInput(attrs={'class': 'form-control'}),
            'placa_vehiculo': forms.TextInput(attrs={'class': 'form-control'}),
        }


class NotaDevolucionItemForm(forms.ModelForm):
    class Meta:
        model = ItemDevolucion
        fields = ['producto', 'almacen_destino', 'cantidad_devuelta', 'estado_fisico', 'motivo']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-select select2'}),
            'almacen_destino': forms.Select(attrs={'class': 'form-select'}),
            'cantidad_devuelta': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'estado_fisico': forms.Select(attrs={'class': 'form-select'}),
            'motivo': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


NotaDevolucionItemFormSet = inlineformset_factory(
    NotaDevolucion, ItemDevolucion,
    form=NotaDevolucionItemForm,
    extra=1,
    can_delete=True
)