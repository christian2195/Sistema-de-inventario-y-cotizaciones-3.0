#!/bin/bash

# ==============================================================================
# SCRIPT DE REVERSIÓN DE ALMACÉN EN RENGLONES - EMVEPRO C.A.
# GERENCIA DE TECNOLOGÍA DE LA INFORMACIÓN Y COMUNICACIÓN (2026)
# ==============================================================================

PROJECT_DIR="/var/www/html/Sistema-de-inventario-y-cotizaciones-3.0"
echo "=== Iniciando restauración del flujo de almacén por renglones ==="
cd $PROJECT_DIR

# 1. SOBREESCRITURA DE CORE/MODELS.PY (Restaurando ItemDespacho original)
echo "[1/4] Restaurando core/models.py..."
cat << 'EOF' > core/models.py
from django.db import models
from django.contrib.auth.models import User
import uuid

class Proveedor(models.Model):
    nombre = models.CharField(max_length=200)
    rif_nit = models.CharField(max_length=50, unique=True, verbose_name="RIF/NIT")
    contacto_principal = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Proveedores"

    def __str__(self):
        return f"{self.nombre} ({self.rif_nit})"

class Cliente(models.Model):
    nombre = models.CharField(max_length=200)
    rif_nit = models.CharField(max_length=50, unique=True, verbose_name="RIF/NIT")
    contacto_principal = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Clientes"

    def __str__(self):
        return f"{self.nombre} ({self.rif_nit})"

class Almacen(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    ubicacion = models.CharField(max_length=255, blank=True, null=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Almacenes"

    def __str__(self):
        return self.nombre

class Producto(models.Model):
    codigo_sku = models.CharField(max_length=50, unique=True, verbose_name="Código/SKU")
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    stock_actual = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Productos"

    def __str__(self):
        return f"[{self.codigo_sku}] {self.nombre}"

class Cotizacion(models.Model):
    ESTATUS_CHOICES = [
        ('PENDIENTE', 'Pendiente por despachar'),
        ('EN_PROCESO', 'En Proceso (Parcialmente Dotado)'),
        ('DOTADO', 'Dotado (Completado)'),
        ('ANULADO', 'Anulado'),
    ]
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='cotizaciones')
    numero_rastreo = models.CharField(max_length=50, unique=True, blank=True, verbose_name="Nro. Nota de Entrega / Cotización")
    referencia_proyecto = models.CharField(max_length=255, blank=True, null=True)
    fecha_emision = models.DateTimeField(auto_now_add=True)
    estatus = models.CharField(max_length=20, choices=ESTATUS_CHOICES, default='PENDIENTE')
    tasa_bcv = models.DecimalField(max_digits=12, decimal_places=4, default=1.0000, verbose_name="Tasa Cambio BCV")
    observacion_tasa = models.CharField(max_length=100, default="BCV")
    incluye_iva = models.BooleanField(default=True, verbose_name="¿Aplica IVA (16%)?")
    subtotal_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    base_imponible_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    monto_iva_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_bs = models.DecimalField(max_digits=16, decimal_places=2, default=0.00)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Cotizaciones"

    def calcular_totales_reales(self):
        items_cot = self.items.all()
        self.subtotal_usd = sum(item.total_item_usd for item in items_cot)
        self.base_imponible_usd = self.subtotal_usd
        if self.incluye_iva:
            self.monto_iva_usd = self.base_imponible_usd * models.Decimal('0.16')
        else:
            self.monto_iva_usd = models.Decimal('0.00')
        self.total_usd = self.base_imponible_usd + self.monto_iva_usd
        self.total_bs = self.total_usd * self.tasa_bcv

    def save(self, *args, **kwargs):
        if not self.numero_rastreo:
            self.numero_rastreo = f"COT-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.numero_rastreo} - {self.cliente.nombre}"

class ItemCotizacion(models.Model):
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name='items')
    seccion_departamento = models.CharField(max_length=150, default="GENERAL")
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad_solicitada = models.DecimalField(max_digits=12, decimal_places=2)
    costo_base_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    factor_margen = models.DecimalField(max_digits=5, decimal_places=2, default=0.10)
    pvp_unitario_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_item_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    cantidad_entregada = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    cantidad_faltante = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    observacion_item = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Ítems de Cotización"

    def save(self, *args, **kwargs):
        if self.costo_base_usd > 0:
            self.pvp_unitario_usd = self.costo_base_usd * (models.Decimal('1.00') + self.factor_margen)
        self.total_item_usd = self.cantidad_solicitada * self.pvp_unitario_usd
        self.cantidad_faltante = self.cantidad_solicitada - self.cantidad_entregada
        super().save(*args, **kwargs)
        self.cotizacion.calcular_totales_reales()
        self.cotizacion.save()

    def __str__(self):
        return f"{self.producto.nombre} - Cant: {self.cantidad_solicitada}"

class ActaRecepcion(models.Model):
    ESTADO_MERCANCIA_CHOICES = [('BUENO', 'Buen Estado'), ('CON_OBSERVACIONES', 'Con Observaciones')]
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, related_name='actas_recepcion')
    almacen = models.ForeignKey(Almacen, on_delete=models.PROTECT, related_name='actas_recepcion')
    numero_factura_proveedor = models.CharField(max_length=100)
    monto_total_factura = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    fecha_recepcion = models.DateTimeField(auto_now_add=True)
    responsable = models.ForeignKey(User, on_delete=models.PROTECT)
    institucion = models.CharField(max_length=200, blank=True, null=True)
    nro_orden_asociada = models.CharField(max_length=100, blank=True, null=True)
    ubicacion_almacen = models.CharField(max_length=100, blank=True, null=True)
    estado_mercancia = models.CharField(max_length=50, choices=ESTADO_MERCANCIA_CHOICES, default='BUENO')
    nombre_conductor = models.CharField(max_length=150, blank=True, null=True)
    cedula_conductor = models.CharField(max_length=20, blank=True, null=True)
    tipo_vehiculo = models.CharField(max_length=100, blank=True, null=True)
    color_vehiculo = models.CharField(max_length=50, blank=True, null=True)
    placa_vehiculo = models.CharField(max_length=50, blank=True, null=True)
    beneficiario_autorizado = models.CharField(max_length=150, blank=True, null=True)
    cedula_beneficiario = models.CharField(max_length=20, blank=True, null=True)
    telefono_beneficiario = models.CharField(max_length=50, blank=True, null=True)
    fecha_hora_llegada_conductor = models.DateTimeField(blank=True, null=True)
    fecha_hora_llegada_beneficiario = models.DateTimeField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Actas de Recepción"

class NotaDespacho(models.Model):
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.PROTECT, related_name='notas_despacho')
    numero_guia = models.CharField(max_length=50, unique=True, verbose_name="Nro. Guía / Despacho")
    fecha_despacho = models.DateTimeField(auto_now_add=True)
    responsable = models.ForeignKey(User, on_delete=models.PROTECT)
    nombre_beneficiario = models.CharField(max_length=200, blank=True, null=True)
    proveedor_origen = models.CharField(max_length=200, blank=True, null=True)
    nro_orden_asociada = models.CharField(max_length=100, blank=True, null=True)
    nombre_conductor = models.CharField(max_length=150, blank=True, null=True)
    cedula_conductor = models.CharField(max_length=20, blank=True, null=True)
    tipo_vehiculo = models.CharField(max_length=100, blank=True, null=True)
    color_vehiculo = models.CharField(max_length=50, blank=True, null=True)
    placa_vehiculo = models.CharField(max_length=50, blank=True, null=True)
    beneficiario_autorizado = models.CharField(max_length=150, blank=True, null=True)
    cedula_beneficiario = models.CharField(max_length=20, blank=True, null=True)
    telefono_beneficiario = models.CharField(max_length=50, blank=True, null=True)
    fecha_hora_llegada_conductor = models.DateTimeField(blank=True, null=True)
    fecha_hora_llegada_beneficiario = models.DateTimeField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Notas de Despacho"

class ItemDespacho(models.Model):
    nota_despacho = models.ForeignKey(NotaDespacho, on_delete=models.CASCADE, related_name='items')
    item_cotizacion = models.ForeignKey(ItemCotizacion, on_delete=models.PROTECT, related_name='despachos')
    cantidad_despachada = models.DecimalField(max_digits=12, decimal_places=2)
    almacen_origen = models.ForeignKey(Almacen, on_delete=models.PROTECT) # <--- RETORNADO COMPLEMENTARIO
    marca = models.CharField(max_length=100, blank=True, null=True)
    modelo = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Ítems de Despacho"

class NotaDevolucion(models.Model):
    nro_devolucion = models.CharField(max_length=50, unique=True)
    origen_devolucion = models.CharField(max_length=200)
    fecha_devolucion = models.DateTimeField(auto_now_add=True)
    motivo_devolucion = models.TextField()
    estado_del_producto = models.CharField(max_length=50, default='APTO')
    nro_orden = models.CharField(max_length=100, blank=True, null=True)
    responsable = models.ForeignKey(User, on_delete=models.PROTECT)
    nombre_conductor = models.CharField(max_length=150, blank=True, null=True)
    cedula_conductor = models.CharField(max_length=20, blank=True, null=True)
    tipo_vehiculo = models.CharField(max_length=100, blank=True, null=True)
    color_vehiculo = models.CharField(max_length=50, blank=True, null=True)
    placa_vehiculo = models.CharField(max_length=50, blank=True, null=True)
    beneficiario_autorizado = models.CharField(max_length=150, blank=True, null=True)
    cedula_beneficiario = models.CharField(max_length=20, blank=True, null=True)
    telefono_beneficiario = models.CharField(max_length=50, blank=True, null=True)
    fecha_hora_llegada_conductor = models.DateTimeField(blank=True, null=True)
    fecha_hora_llegada_beneficiario = models.DateTimeField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Notas de Devolución"

class ItemDevolucion(models.Model):
    nota_devolucion = models.ForeignKey(NotaDevolucion, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='items_devueltos')
    cantidad = models.DecimalField(max_digits=12, decimal_places=2)
    marca = models.CharField(max_length=100, blank=True, null=True)
    modelo = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Ítems de Devolución"

class MovimientoInventario(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='movimientos')
    almacen = models.ForeignKey(Almacen, on_delete=models.PROTECT, related_name='movimientos')
    tipo = models.CharField(max_length=15)
    cantidad = models.DecimalField(max_digits=12, decimal_places=2)
    costo_unitario = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    fecha_movimiento = models.DateTimeField(auto_now_add=True)
    responsable = models.ForeignKey(User, on_delete=models.PROTECT)
    acta_recepcion = models.ForeignKey(ActaRecepcion, on_delete=models.CASCADE, null=True, blank=True)
    nota_despacho = models.ForeignKey(NotaDespacho, on_delete=models.CASCADE, null=True, blank=True)
    nota_devolucion = models.ForeignKey(NotaDevolucion, on_delete=models.CASCADE, null=True, blank=True)
    observacion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Movimientos de Inventario"

class PagoProveedor(models.Model):
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, related_name='pagos')
    monto_pagado = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_pago = models.DateTimeField(auto_now_add=True)
    referencia_pago = models.CharField(max_length=100)
    responsable = models.ForeignKey(User, on_delete=models.PROTECT)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Pagos a Proveedores"
EOF

# 2. SOBREESCRITURA DE CORE/FORMS.PY
echo "[2/4] Restaurando core/forms.py..."
cat << 'EOF' > core/forms.py
from django import forms
from django.forms import inlineformset_factory
from .models import Producto, Cotizacion, ItemCotizacion, NotaDespacho, ItemDespacho

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['codigo_sku', 'nombre', 'descripcion', 'stock_actual', 'activo']

class CotizacionForm(forms.ModelForm):
    class Meta:
        model = Cotizacion
        fields = ['cliente', 'referencia_proyecto', 'tasa_bcv', 'observacion_tasa', 'incluye_iva', 'observaciones', 'estatus']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-select select2'}),
            'referencia_proyecto': forms.TextInput(attrs={'class': 'form-control'}),
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

ItemCotizacionFormSet = inlineformset_factory(Cotizacion, ItemCotizacion, form=ItemCotizacionForm, extra=1, can_delete=True)

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
EOF

# 3. SOBREESCRITURA DE CORE/VIEWS.PY
echo "[3/4] Sincronizando core/views.py con almacen_origen..."
sed -i "s/fields=\['item_cotizacion', 'cantidad_despachada', 'marca', 'modelo'\]/fields=\['item_cotizacion', 'almacen_origen', 'cantidad_despachada', 'marca', 'modelo'\]/g" core/views.py

# 4. SOBREESCRITURA DE DESPACHO_FORM.HTML
echo "[4/4] Restaurando core/templates/core/despacho_form.html..."
cat << 'EOF' > core/templates/core/despacho_form.html
{% extends 'core/base.html' %}
{% load crispy_forms_tags %}

{% block title %}Nota de Despacho | EMVEPRO{% endblock %}

{% block content %}
<div class="container-fluid animate__animated animate__fadeIn">
    <div class="d-flex justify-content-between align-items-center mb-4 border-bottom pb-3">
        <h2 class="text-warning fw-bold mb-0 text-dark">
            <i class="bi bi-truck me-2 text-warning"></i> Procesar Despacho de Carga (Salida)
        </h2>
        <span class="badge bg-dark p-2 shadow-sm fs-6">
            <i class="bi bi-shield-lock-fill text-warning me-1"></i> Almacén Fuerte Tiuna
        </span>
    </div>

    <form method="POST" id="despacho-form">
        {% csrf_token %}
        
        <div class="row g-4">
            <div class="col-lg-5">
                <div class="card shadow border-0 border-top border-warning border-4 mb-4">
                    <div class="card-header bg-white py-3">
                        <h5 class="mb-0 fw-bold text-secondary"><i class="bi bi-person-badge-fill me-2"></i> Control de Logística y Conductor</h5>
                    </div>
                    <div class="card-body bg-light-subtle">
                        {{ form|crispy }}
                    </div>
                </div>
            </div>

            <div class="col-lg-7">
                <div class="card shadow border-0 border-top border-dark border-4 h-100 d-flex flex-column">
                    <div class="card-header bg-white py-3 d-flex justify-content-between align-items-center">
                        <h5 class="mb-0 fw-bold text-secondary"><i class="bi bi-cart-dash-fill me-2"></i> Artículos Autorizados para Salida</h5>
                        <button type="button" id="add-item-btn" class="btn btn-dark btn-sm fw-bold shadow-sm text-warning">
                            <i class="bi bi-plus-lg me-1"></i> Agregar Renglón
                        </button>
                    </div>
                    
                    <div class="card-body bg-light p-3 flex-grow-1" style="max-height: 650px; overflow-y: auto;" id="formset-container">
                        {{ formset.management_form }}
                        
                        {% for item_form in formset %}
                        <div class="card item-row-card mb-3 border-start border-warning border-3 shadow-sm position-relative animate__animated animate__fadeInUp">
                            <div class="card-body p-3">
                                {% for hidden in item_form.hidden_fields %}{{ hidden }}{% endfor %}
                                
                                <div class="row g-3">
                                    <div class="col-md-12">
                                        <label class="form-label fw-bold text-muted small">Vínculo con Renglón de Cotización</label>
                                        {{ item_form.item_cotizacion }}
                                    </div>
                                    <div class="col-md-6">
                                        <label class="form-label fw-bold text-muted small">Almacén de Depósito Origen</label>
                                        {{ item_form.almacen_origen }}
                                    </div>
                                    <div class="col-md-6">
                                        <label class="form-label fw-bold text-muted small">Cantidad Física a Extraer</label>
                                        {{ item_form.cantidad_despachada }}
                                    </div>
                                    <div class="col-md-6">
                                        <label class="form-label fw-bold text-muted small">Marca del Producto</label>
                                        {{ item_form.marca }}
                                    </div>
                                    <div class="col-md-6">
                                        <label class="form-label fw-bold text-muted small">Modelo / Nro Serial</label>
                                        {{ item_form.modelo }}
                                    </div>
                                </div>

                                <div class="position-absolute top-0 end-0 p-2">
                                    {% if item_form.instance.pk %}
                                        <div class="form-check text-danger bg-danger-subtle p-1 px-2 rounded small border border-danger-subtle">
                                            {{ item_form.DELETE }} <label class="form-check-label small font-monospace">Quitar</label>
                                        </div>
                                    {% endif %}
                                </div>
                            </div>
                        </div>
                        {% endfor %}
                    </div>

                    <div class="card-footer bg-white py-3 text-end">
                        <a href="{% url 'core:estatus_proyectos' %}" class="btn btn-secondary px-4 me-2 shadow-sm">Cancelar</a>
                        <button type="submit" class="btn btn-warning btn-lg px-4 text-dark fw-bold shadow">
                            <i class="bi bi-shield-check me-1"></i> Emitir Guía y Despachar Carga
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </form>
</div>

<div id="empty-form" style="display: none;">
    <div class="card item-row-card mb-3 border-start border-warning border-3 shadow-sm position-relative animate__animated animate__fadeInUp">
        <div class="card-body p-3">
            <div class="row g-3">
                <div class="col-md-12">
                    <label class="form-label fw-bold text-muted small">Vínculo con Renglón de Cotización</label>
                    {{ formset.empty_form.item_cotizacion }}
                </div>
                <div class="col-md-6">
                    <label class="form-label fw-bold text-muted small">Almacén de Depósito Origen</label>
                    {{ formset.empty_form.almacen_origen }}
                </div>
                <div class="col-md-6">
                    <label class="form-label fw-bold text-muted small">Cantidad Física a Extraer</label>
                    {{ formset.empty_form.cantidad_despachada }}
                </div>
                <div class="col-md-6">
                    <label class="form-label fw-bold text-muted small">Marca del Producto</label>
                    {{ formset.empty_form.marca }}
                </div>
                <div class="col-md-6">
                    <label class="form-label fw-bold text-muted small">Modelo / Nro Serial</label>
                    {{ formset.empty_form.modelo }}
                </div>
            </div>
        </div>
    </div>
</div>

<script>
    document.addEventListener("DOMContentLoaded", function() {
        const addButton = document.getElementById('add-item-btn');
        const container = document.getElementById('formset-container');
        const totalForms = document.getElementById('id_items-TOTAL_FORMS'); 
        const emptyFormTemplate = document.getElementById('empty-form').innerHTML;

        addButton.addEventListener('click', function(e) {
            e.preventDefault();
            const formCount = parseInt(totalForms.value);
            const newRow = emptyFormTemplate.replace(/__prefix__/g, formCount);
            container.insertAdjacentHTML('beforeend', newRow);
            totalForms.value = formCount + 1;
        });
    });
</script>
{% endblock %}
EOF

# 5. MIGRACIONES Y REINICIO DE SERVICIOS
echo "=== Compilando y ejecutando migraciones de base de datos ==="
venv/bin/python manage.py makemigrations
venv/bin/python manage.py migrate
venv/bin/python manage.py check

echo "=== Reiniciando Gunicorn (Producción) ==="
sudo systemctl restart gunicorn

echo "=== ¡PROCESO DE REVERSIÓN COMPLETADO CON ÉXITO! ==="