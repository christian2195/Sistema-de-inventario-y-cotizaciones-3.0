#!/bin/bash

echo "====================================================="
echo "   DIAGNÓSTICO DE ARCHIVOS MEDIA (DJANGO + NGINX)    "
echo "====================================================="

PROJECT_DIR="/var/www/html/Sistema-de-inventario-y-cotizaciones-3.0"
MEDIA_DIR="$PROJECT_DIR/media"

echo -e "\n1. VERIFICANDO DIRECTORIO Y PERMISOS..."
if [ -d "$MEDIA_DIR" ]; then
    echo "✅ [OK] La carpeta media existe."
    
    # Verificar propietario
    PROPIETARIO=$(stat -c '%U:%G' "$MEDIA_DIR")
    echo "   -> Propietario actual: $PROPIETARIO"
    if [[ "$PROPIETARIO" == *"www-data"* ]]; then
        echo "✅ [OK] Nginx (www-data) tiene la propiedad de la carpeta."
    else
        echo "❌ [ERROR] El propietario no es www-data. Nginx no puede leer las fotos."
        echo "   -> Solución: Ejecuta 'sudo chown -R www-data:www-data $MEDIA_DIR'"
    fi
    
    # Verificar permisos de lectura
    PERMISOS=$(stat -c '%a' "$MEDIA_DIR")
    echo "   -> Permisos actuales: $PERMISOS"
    if [ "$PERMISOS" -ge 755 ]; then
        echo "✅ [OK] Los permisos de lectura pública son correctos."
    else
        echo "❌ [ERROR] Los permisos son muy restrictivos."
        echo "   -> Solución: Ejecuta 'sudo chmod -R 755 $MEDIA_DIR'"
    fi
else
    echo "❌ [ERROR] La carpeta $MEDIA_DIR NO existe."
    echo "   -> Solución: Verifica tu variable MEDIA_ROOT en settings.py"
fi

echo -e "\n2. REVISANDO FOTOGRAFÍAS SUBIDAS..."
if [ -d "$MEDIA_DIR/productos" ]; then
    CANTIDAD=$(ls -1q "$MEDIA_DIR/productos" | wc -l)
    echo "📸 Hay $CANTIDAD imágenes en la carpeta de productos."
    echo "Últimos 3 archivos:"
    ls -lh "$MEDIA_DIR/productos" | tail -n 3
else
    echo "⚠️ [ADVERTENCIA] La subcarpeta 'productos' no existe aún."
fi

echo -e "\n3. VERIFICANDO CONFIGURACIÓN DE NGINX..."
NGINX_CHECK=$(grep -R "location /media" /etc/nginx/sites-enabled/ 2>/dev/null)

if [ -n "$NGINX_CHECK" ]; then
    echo "✅ [OK] Nginx tiene configurada la ruta /media/:"
    echo "   -> $NGINX_CHECK"
else
    echo "❌ [ERROR] Nginx NO está configurado para servir la carpeta /media/."
    echo "   -> Solución: Debes agregar el bloque 'location /media/ { ... }' en tu archivo de Nginx."
fi

echo -e "\n====================================================="
echo "               PRUEBA DE SINTAXIS NGINX              "
echo "====================================================="
sudo nginx -t

echo -e "\nFIN DEL DIAGNÓSTICO."
