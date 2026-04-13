#!/bin/bash
# ============================================
# AMAPICKS - Script de Despliegue con PM2
# Ejecutar en la VPS: bash deploy.sh
# ============================================

set -e  # Detener si hay errores

PROJECT_DIR="/home/amarelita/amapicks"
FRONTEND_DIR="$PROJECT_DIR/web/frontend"
LOGS_DIR="$PROJECT_DIR/logs"
VENV_PYTHON="$PROJECT_DIR/venv/bin/python"
VENV_PIP="$PROJECT_DIR/venv/bin/pip"

echo "=========================================="
echo "  AMAPICKS - Desplegando con PM2..."
echo "=========================================="

# 1. Crear directorio de logs si no existe
if [ ! -d "$LOGS_DIR" ]; then
    echo "📁 Creando directorio de logs..."
    mkdir -p "$LOGS_DIR"
fi

# 2. Ir al directorio del proyecto
cd "$PROJECT_DIR"

# 3. Traer últimos cambios de GitHub
echo ""
echo "[1/4] 📥 Descargando cambios de GitHub..."
git pull origin main

# 4. Actualizar dependencias Python
echo ""
echo "[2/4] 🐍 Actualizando dependencias Python..."
$VENV_PIP install -r requirements.txt --quiet

# 5. Compilar frontend si existe
if [ -d "$FRONTEND_DIR" ]; then
    echo ""
    echo "[3/4] ⚛️ Compilando frontend..."
    cd "$FRONTEND_DIR"
    npm install --silent
    npm run build
    cd "$PROJECT_DIR"
fi

# 6. Iniciar o reiniciar servicios con PM2
echo ""
echo "[4/4] 🚀 Iniciando/Reiniciando servicios PM2..."

# Intentar reiniciar usando el archivo de configuración
pm2 restart ecosystem.config.js || pm2 start ecosystem.config.js
pm2 save

echo ""
echo "=========================================="
echo "  ✅ Despliegue AMAPICKS completado"
echo "=========================================="
echo ""
echo "📊 Estado de los servicios:"
pm2 status
echo ""
echo "📝 Comandos útiles:"
echo "   Ver logs:        pm2 logs"
echo "   Ver logs bot:    pm2 logs gbleagues-bot"
echo "   Monitoreo:       pm2 monit"
echo ""
echo "📁 Logs ubicados en: $LOGS_DIR"
echo ""
