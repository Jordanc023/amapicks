#!/bin/bash
# ============================================
# AMAPICKS - Script de Despliegue
# Ejecutar en la VPS: bash deploy.sh
# ============================================

set -e  # Detener si hay errores

PROJECT_DIR="/home/jordanvps/amapicks"
FRONTEND_DIR="$PROJECT_DIR/web/frontend"

echo "=========================================="
echo "  AMAPICKS - Desplegando..."
echo "=========================================="

# 1. Ir al directorio del proyecto
cd "$PROJECT_DIR"

# 2. Traer últimos cambios de GitHub
echo ""
echo "[1/4] Descargando cambios de GitHub..."
git pull origin main

# 3. Instalar dependencias Python si requirements.txt cambió
echo ""
echo "[2/4] Actualizando dependencias Python..."
pip install -r requirements.txt --quiet

# 4. Instalar y compilar frontend si cambió
echo ""
echo "[3/4] Compilando frontend..."
cd "$FRONTEND_DIR"
npm install --silent
npm run build
cd "$PROJECT_DIR"

# 5. Reiniciar servicios con PM2
echo ""
echo "[4/4] Reiniciando servicios..."
pm2 restart ecosystem.config.js

echo ""
echo "=========================================="
echo "  ✅ Despliegue completado exitosamente"
echo "=========================================="
pm2 status
