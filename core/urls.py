from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Cambiamos '' por 'dashboard/' para que sea una ruta explícita y segura
    path('dashboard/', views.dashboard_principal, name='dashboard'),
    
    path('proyectos/', views.estatus_proyectos, name='estatus_proyectos'),
    path('proveedores/finanzas/', views.finanzas_proveedores, name='finanzas_proveedores'),
    path('productos/', views.lista_productos, name='lista_productos'),
    path('productos/nuevo/', views.crear_producto, name='crear_producto'),
    path('cotizaciones/nueva/', views.crear_cotizacion, name='crear_cotizacion'),
    path('recepcion/nueva/', views.crear_acta_recepcion, name='crear_acta_recepcion'),
    path('despacho/nuevo/', views.crear_nota_despacho, name='crear_nota_despacho'),
    path('despacho/<int:despacho_id>/pdf/', views.generar_pdf_despacho, name='despacho_pdf'),
    path('cotizaciones/<int:cotizacion_id>/pdf/', views.generar_pdf_cotizacion, name='cotizacion_pdf'),
    # Añade esta línea dentro de urlpatterns de tu core/urls.py
    path('devolucion/nueva/', views.crear_nota_devolucion, name='crear_nota_devolucion'),
    path('despacho/nuevo/', views.crear_nota_despacho, name='crear_nota_despacho'),
    # Rutas para la creación de Entes/Proyectos y Proveedores
    path('cliente/nuevo/', views.crear_cliente, name='crear_cliente'),
    path('proveedor/nuevo/', views.crear_proveedor, name='crear_proveedor'),
    path('almacen/nuevo/', views.crear_almacen, name='crear_almacen'),
    path('api/cotizacion/<int:cotizacion_id>/productos/', views.api_productos_cotizacion, name='api_productos_cotizacion'),
    path('productos/carga-masiva/', views.carga_masiva_productos, name='carga_masiva_productos'),
]