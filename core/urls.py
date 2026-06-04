from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard_principal, name='dashboard'),
    path('proyectos/', views.estatus_proyectos, name='estatus_proyectos'),
]