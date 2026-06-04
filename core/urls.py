from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard_principal, name='dashboard'),
    path('proyectos/', views.estatus_proyectos, name='estatus_proyectos'),
    path('proveedores/finanzas/', views.finanzas_proveedores, name='finanzas_proveedores'),
    path('productos/', views.lista_productos, name='lista_productos'),
    path('productos/nuevo/', views.crear_producto, name='crear_producto'),
    path('cotizaciones/nueva/', views.crear_cotizacion, name='crear_cotizacion'),
    path('recepcion/nueva/', views.crear_acta_recepcion, name='crear_acta_recepcion'),
    path('despacho/nuevo/', views.crear_nota_despacho, name='crear_nota_despacho'),
    path('cotizaciones/<int:cotizacion_id>/pdf/', views.generar_pdf_cotizacion, name='cotizacion_pdf'),
]