#!/bin/bash
# ============================================
# GBLEAGUES - Script de Despliegue con PM2
# Ejecutar en la VPS: bash deploy.sh
# ============================================

set -e  # Detener si hay errores

PROJECT_DIR="/home/jordanvps/gbleagues"
FRONTEND_DIR="$PROJECT_DIR/web/frontend"
LOGS_DIR="$PROJECT_DIR/logs"
VENV_PYTHON="$PROJECT_DIR/venv/bin/python"
VENV_PIP="$PROJECT_DIR/venv/bin/pip"

echo "=========================================="
echo "  GBLEAGUES - Desplegando con PM2..."
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
echo "[1/5] 📥 Descargando cambios de GitHub..."
git pull origin main

# 4. Instalar dependencias Python si requirements.txt cambió
echo ""
echo "[2/5] 🐍 Actualizando dependencias Python..."
$VENV_PIP install -r requirements.txt --quiet

# 5. Instalar y compilar frontend si cambió
echo ""
echo "[3/5] ⚛️ Compilando frontend..."
cd "$FRONTEND_DIR"
npm install --silent
npm run build
cd "$PROJECT_DIR"

# 6. Instalar serve globalmente si no existe (para el frontend)
echo ""
echo "[4/5] 🔧 Verificando serve..."
if ! command -v npx &> /dev/null || ! npx serve --version &> /dev/null 2>&1; then
    echo "   Instalando serve..."
    npm install -g serve
fi

# 7. Iniciar o reiniciar servicios con PM2
echo ""
echo "[5/5] 🚀 Iniciando/Reiniciando servicios PM2..."

# Verificar si PM2 ya tiene los procesos
if pm2 describe gbleagues-bot &> /dev/null; then
    echo "   Reiniciando procesos existentes..."
    pm2 restart ecosystem.config.js
else
    echo "   Iniciando procesos por primera vez..."
    pm2 start ecosystem.config.js
    pm2 save
fi

echo ""
echo "=========================================="
echo "  ✅ Despliegue GBLEAGUES completado exitosamente"
echo "=========================================="
echo ""
echo "📊 Estado de los servicios:"
pm2 status
echo ""
echo "📝 Comandos útiles:"
echo "   Ver logs:        pm2 logs"
echo "   Ver logs bot:    pm2 logs gbleagues-bot"
echo "   Monitoreo:       pm2 monit"
echo "   Detener todo:    pm2 stop all"
echo "   Reiniciar todo:  pm2 restart all"
echo ""
echo "📁 Logs ubicados en: $LOGS_DIR"
echo ""
