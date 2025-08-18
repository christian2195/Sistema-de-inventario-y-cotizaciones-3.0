# inventario/urls.py

from django.urls import path
from . import views
from django.contrib.auth import views as auth_views # Importar las vistas de autenticación de Django
from django.views.generic.base import RedirectView
from django.urls import reverse_lazy

app_name = 'inventario' # Define el nombre de la aplicación para usar en reverse_lazy

urlpatterns = [
    # Redirección para /inventario/ a /inventario/dashboard/
    path('', RedirectView.as_view(url=reverse_lazy('inventario:dashboard'), permanent=True)),

    # URLs de Autenticación
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),

    # URLs existentes para productos
    path('productos/', views.ProductoListView.as_view(), name='product_list'),
    path('productos/crear/', views.ProductoCreateView.as_view(), name='product_create'),
    path('productos/<int:pk>/', views.ProductoDetailView.as_view(), name='product_detail'),
    path('productos/<int:pk>/editar/', views.ProductoUpdateView.as_view(), name='product_update'),
    path('productos/<int:pk>/eliminar/', views.ProductoDeleteView.as_view(), name='product_delete'),
    path('productos/exportar-excel/', views.export_productos_excel, name='export_productos_excel'),
    path('productos/exportar-pdf/', views.export_productos_pdf, name='export_productos_pdf'),
    path('productos/importar-excel/', views.import_productos_excel, name='import_productos_excel'),
    path('productos/exportar-etiquetas-pdf/', views.export_product_labels_pdf, name='export_product_labels_pdf'),
    # URL para obtener la lista de productos en formato JSON
    path('api/productos/list/', views.product_list_json, name='api_product_list'),


    # URLs existentes para movimientos
    path('movimientos/', views.MovimientoListView.as_view(), name='movimiento_list'),
    path('movimientos/crear/', views.MovimientoCreateView.as_view(), name='movimiento_create'),
    path('movimientos/<int:pk>/', views.MovimientoDetailView.as_view(), name='movimiento_detail'),
    path('movimientos/<int:pk>/editar/', views.MovimientoUpdateView.as_view(), name='movimiento_update'),
    path('movimientos/<int:pk>/eliminar/', views.MovimientoDeleteView.as_view(), name='movimiento_delete'),
    path('movimientos/importar-excel/', views.import_movimientos_excel, name='import_movimientos_excel'),
    path('movimientos/exportar-excel/', views.export_movimientos_excel, name='export_movimientos_excel'),
    path('movimientos/exportar-pdf/', views.export_movimientos_pdf, name='export_movimientos_pdf'),

    # URLs existentes para guías de salida
    path('guias-salida/', views.GuiaSalidaListView.as_view(), name='guia_salida_list'),
    path('guias-salida/crear/', views.GuiaSalidaCreateView.as_view(), name='guia_salida_create'),
    path('guias-salida/<int:pk>/', views.GuiaSalidaDetailView.as_view(), name='guia_salida_detail'),
    path('guias-salida/<int:pk>/editar/', views.GuiaSalidaUpdateView.as_view(), name='guia_salida_update'),
    path('guias-salida/<int:pk>/eliminar/', views.GuiaSalidaDeleteView.as_view(), name='guia_salida_delete'),

      # URLs para Notas de Despacho (Nueva interfaz de creación)
    path('notas-despacho/crear/', views.NotaDespachoInterfaceView.as_view(), name='nota_despacho_create'),
    path('notas-despacho/editar/<int:pk>/', views.NotaDespachoInterfaceView.as_view(), name='nota_despacho_update'),
    path('api/notas-despacho/crear/', views.create_nota_despacho_from_interface, name='create_nota_despacho_from_interface'),
    path('api/productos-for-dispatch/', views.get_product_list_for_dispatch, name='get_product_list_for_dispatch'),
    path('notas-despacho/', views.NotaDespachoListView.as_view(), name='nota_despacho_list'),
    path('notas-despacho/exportar-excel/', views.export_notas_despacho_excel, name='export_notas_despacho_excel'),
    path('notas-despacho/<int:pk>/', views.NotaDespachoDetailView.as_view(), name='nota_despacho_detail'),
    path('notas-despacho/<int:pk>/eliminar/', views.NotaDespachoDeleteView.as_view(), name='nota_despacho_delete'),
    # API para obtener detalles de cotización (se mantiene)
    path('api/cotizaciones/<int:pk>/details/', views.get_cotizacion_details_api, name='api_cotizacion_details'),
    path('get-productos-from-cotizacion/<int:pk>/', views.get_productos_from_cotizacion, name='get_productos_from_cotizacion'),

    # URLs para órdenes de salida (solo detalle, la creación es automática desde cotización)
    path('ordenes-salida/<int:pk>/', views.OrdenSalidaDetailView.as_view(), name='orden_salida_detail'),

    # URLs para Actas de Recepción
    path('actas-recepcion/', views.ActaRecepcionListView.as_view(), name='acta_recepcion_list'),
    path('actas-recepcion/crear/', views.ActaRecepcionCreateView.as_view(), name='acta_recepcion_create'),
    path('actas-recepcion/<int:pk>/', views.ActaRecepcionDetailView.as_view(), name='acta_recepcion_detail'),
    path('actas-recepcion/<int:pk>/editar/', views.ActaRecepcionUpdateView.as_view(), name='acta_recepcion_update'),
    path('actas-recepcion/<int:pk>/eliminar/', views.ActaRecepcionDeleteView.as_view(), name='acta_recepcion_delete'),
    path('actas-recepcion/<int:pk>/exportar-pdf/', views.export_acta_recepcion_pdf, name='export_acta_recepcion_pdf'),

    # URLs para Clientes
    path('clientes/', views.ClienteListView.as_view(), name='cliente_list'),
    path('clientes/crear/', views.ClienteCreateView.as_view(), name='cliente_create'),
    path('clientes/<int:pk>/', views.ClienteDetailView.as_view(), name='cliente_detail'),
    path('clientes/<int:pk>/editar/', views.ClienteUpdateView.as_view(), name='cliente_update'),
    path('clientes/<int:pk>/eliminar/', views.ClienteDeleteView.as_view(), name='cliente_delete'),

    # URLs para Cotizaciones
    path('cotizaciones/', views.CotizacionListView.as_view(), name='cotizacion_list'),
    path('cotizaciones/crear/', views.CotizacionCreateView.as_view(), name='cotizacion_create'),
    path('cotizaciones/<int:pk>/', views.CotizacionDetailView.as_view(), name='cotizacion_detail'),
    path('cotizaciones/<int:pk>/editar/', views.CotizacionUpdateView.as_view(), name='cotizacion_update'),
    path('cotizaciones/<int:pk>/eliminar/', views.CotizacionDeleteView.as_view(), name='cotizacion_delete'),
    path('cotizaciones/<int:pk>/aceptar/', views.cotizacion_accept, name='cotizacion_accept'),
    # URL para la interfaz de cotizaciones (Mini POS original)
    path('cotizaciones/interface/', views.CotizacionesInterfaceView.as_view(), name='cotizaciones_interface'),
    path('cotizaciones/create_from_interface/', views.create_cotizacion_from_interface, name='create_cotizacion_from_interface'),
    # Esta es la URL corregida para la vista de detalles en JSON
    path('cotizaciones/<int:pk>/json/', views.cotizacion_detail_json, name='cotizacion_detail_json'),

    # URLs para Pagos a Proveedores
    path('pagos-proveedor/', views.PagoProveedorListView.as_view(), name='pago_proveedor_list'),
    path('pagos-proveedor/crear/', views.PagoProveedorCreateView.as_view(), name='pago_proveedor_create'),
    path('pagos-proveedor/<int:pk>/', views.PagoProveedorDetailView.as_view(), name='pago_proveedor_detail'),
    path('pagos-proveedor/<int:pk>/editar/', views.PagoProveedorUpdateView.as_view(), name='pago_proveedor_update'),
    path('pagos-proveedor/<int:pk>/eliminar/', views.PagoProveedorDeleteView.as_view(), name='pago_proveedor_delete'),

    # URL del Dashboard
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),

    # URL para el Panel de Gestión de Proveedores
    path('proveedores/gestion/', views.ProveedorManagementView.as_view(), name='proveedor_management_panel'),

    # Rutas para Movimientos
    path('movimientos/crear/', views.movimiento_crear, name='movimiento_crear'),
    path('api/movimiento/crear/', views.crear_movimiento_from_interface, name='crear_movimiento_from_interface'),

    # APIs para el formulario de Nota de Despacho (actualizado)
    path('api/productos/despacho/', views.api_get_products_for_dispatch, name='api_get_products_for_dispatch'),
    path('api/add-detalle-form/', views.api_add_detalle_form, name='api_add_detalle_form'),
    path('api/orden-salida/<int:pk>/detalles/', views.api_get_orden_salida_details, name='api_get_orden_salida_details'),
]

# Define los manejadores de errores personalizados
# Asegúrate de que estas vistas existan en tu inventario/views.py
handler404 = 'inventario.views.custom_404_view'
handler500 = 'inventario.views.custom_500_view'