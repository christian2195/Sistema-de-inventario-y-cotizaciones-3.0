from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # ==========================================
    # DASHBOARD PRINCIPAL
    # ==========================================
    path('dashboard/', views.dashboard_principal, name='dashboard'),
    
    # ==========================================
    # FINANZAS E INSTITUCIONES
    # ==========================================
    path('proyectos/', views.estatus_proyectos, name='estatus_proyectos'),
    path('proveedores/finanzas/', views.finanzas_proveedores, name='finanzas_proveedores'),
    
    # ==========================================
    # OPERACIONES DE CATÁLOGO
    # ==========================================
    path('productos/', views.lista_productos, name='lista_productos'),
    path('productos/nuevo/', views.crear_producto, name='crear_producto'),
    path('productos/carga-masiva/', views.carga_masiva_productos, name='carga_masiva_productos'),
    path('productos/<int:producto_id>/editar/', views.editar_producto, name='editar_producto'),
    # ==========================================
    # MOVIMIENTOS LOGÍSTICOS (INTERFAZ POS)
    # ==========================================
    path('cotizaciones/nueva/', views.crear_cotizacion, name='crear_cotizacion'),
    path('cotizaciones/<int:cotizacion_id>/pdf2/', views.generar_pdf_cotizacion_2, name='generar_pdf_cotizacion_2'),
    path('recepcion/nueva/', views.crear_acta_recepcion, name='crear_acta_recepcion'),
    path('despacho/nuevo/', views.crear_nota_despacho, name='crear_nota_despacho'),
    path('devolucion/nueva/', views.crear_nota_devolucion, name='crear_nota_devolucion'),
    path('cotizaciones/', views.lista_cotizaciones, name='lista_cotizaciones'),
    path('cotizaciones/<int:cotizacion_id>/editar/', views.editar_cotizacion, name='editar_cotizacion'),
    # ==========================================
    # GENERACIÓN DE DOCUMENTOS PDF
    # ==========================================
    path('cotizaciones/<int:cotizacion_id>/pdf/', views.generar_pdf_cotizacion, name='generar_pdf_cotizacion'),
    path('despacho/<int:despacho_id>/pdf/', views.generar_pdf_despacho, name='despacho_pdf'),
    # path('recepcion/<int:recepcion_id>/pdf/', views.generar_pdf_recepcion, name='recepcion_pdf'),
    # path('devolucion/<int:devolucion_id>/pdf/', views.generar_pdf_devolucion, name='devolucion_pdf'),
    
    # ==========================================
    # REGISTROS BASE
    # ==========================================
    path('cliente/nuevo/', views.crear_cliente, name='crear_cliente'),
    path('proveedor/nuevo/', views.crear_proveedor, name='crear_proveedor'),
    path('almacen/nuevo/', views.crear_almacen, name='crear_almacen'),
    
    # ==========================================
    # APIs Y ENDPOINTS DINÁMICOS
    # ==========================================
    path('api/cotizacion/<int:cotizacion_id>/productos/', views.api_productos_cotizacion, name='api_productos_cotizacion'),

    path('usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('usuarios/nuevo/', views.crear_usuario, name='crear_usuario'),
    path('usuarios/<int:pk>/editar/', views.editar_usuario, name='editar_usuario'),
]