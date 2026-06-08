from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 1. LA RAÍZ REDIRIGE DIRECTO AL LOGIN
    # Al entrar a http://proyectos.emvepro.gob.ve/ se enviará de inmediato a /accounts/login/
    path('', RedirectView.as_view(url='/accounts/login/', permanent=False)),
    
    # 2. Las rutas operativas de EMVEPRO (Dashboard, Productos, etc.)
    path('core/', include('core.urls')),
    
    # 3. Rutas del sistema de autenticación de Django
    path('accounts/', include('django.contrib.auth.urls')),
    
    # 4. Redirección de contingencia por si quedó algún rastro de la app vieja
    path('inventario/dashboard/', RedirectView.as_view(pattern_name='core:dashboard', permanent=False)),
]