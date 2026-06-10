import os
import sys
import subprocess
import socket

def ejecutar_comando(comando):
    try:
        resultado = subprocess.run(comando, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return True, resultado.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stderr.strip()

print("=" * 60)
print("SISTEMA DE DIAGNÓSTICO DE INFRAESTRUCTURA - EMVEPRO")
print("=" * 60)

# 1. VERIFICAR RUTAS CLAVE
ruta_proyecto = "/var/www/html/Sistema-de-inventario-y-cotizaciones-3.0"
print("\n[1] Verificando Rutas y Archivos...")
if os.path.exists(ruta_proyecto):
    print(f"  ✓ Carpeta del proyecto encontrada: {ruta_proyecto}")
else:
    print(f"  ✗ ERROR: No existe la carpeta del proyecto en {ruta_proyecto}")

wsgi_path = os.path.join(ruta_proyecto, "emvepro_sys/wsgi.py")
if os.path.exists(wsgi_path):
    print("  ✓ Archivo wsgi.py de Django detectado correctamente.")
else:
    print("  ✗ ERROR: No se encuentra emvepro_sys/wsgi.py. ¿Tu carpeta principal se llama distinto?")

# 2. PROBAR EL ENTORNO VIRTUAL Y DJANGO
print("\n[2] Probando Entorno Virtual y Sintaxis de Django...")
venv_python = os.path.join(ruta_proyecto, "venv/bin/python3")
if os.path.exists(venv_python):
    cmd_django = f"{venv_python} {ruta_proyecto}/manage.py check"
    success, out = ejecutar_comando(cmd_django)
    if success:
        print("  ✓ Django Check exitoso: La sintaxis del código y settings.py están perfectas.")
    else:
        print(f"  ✗ ERROR en el código Django/Settings:\n{out}")
else:
    print("  ✗ ERROR: No se encontró el ejecutable de Python en el venv.")

# 3. VERIFICAR ESTADO DE LOS SERVICIOS
print("\n[3] Verificando Estado de los Servicios en Systemd...")
_, gunicorn_status = ejecutar_comando("systemctl is-active gunicorn")
print(f"  • Gunicorn está: {gunicorn_status.upper()}")

_, nginx_status = ejecutar_comando("systemctl is-active nginx")
print(f"  • Nginx está: {nginx_status.upper()}")

# 4. ANALIZAR EL ARCHIVO SOCKET
print("\n[4] Analizando el Archivo Socket (.sock)...")
socket_path = os.path.join(ruta_proyecto, "emvepro.sock")
if os.path.exists(socket_path):
    stat_info = os.stat(socket_path)
    permisos = oct(stat_info.st_mode)[-3:]
    print(f"  ✓ Archivo emvepro.sock encontrado.")
    print(f"  • Permisos actuales del socket: {permisos}")
    
    # Probar si Nginx puede conectarse al socket
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(socket_path)
        print("  ✓ Conexión exitosa: El socket responde peticiones.")
        s.close()
    except Exception as e:
        print(f"  ✗ ERROR: El archivo socket existe pero no responde conexiones: {e}")
else:
    print("  ✗ ERROR: El archivo emvepro.sock NO EXISTE. Gunicorn no lo está creando.")

# 5. DIAGNÓSTICO DE CONFIGURACIÓN NGINX
print("\n[5] Verificando Configuración de Nginx...")
success, out = ejecutar_comando("sudo nginx -t")
if success:
    print("  ✓ Configuración de Nginx válida sintácticamente.")
else:
    print(f"  ✗ ERROR en configuración de Nginx:\n{out}")

print("\n" + "=" * 60)
