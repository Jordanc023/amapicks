#!/bin/bash
# ============================================
# GBLEAGUES - Setup Inicial para VPS Limpia
# Ejecutar: bash setup.sh
# ============================================

set -e

echo "=========================================="
echo "  GBLEAGUES - Configuración Inicial"
echo "=========================================="

# 1. Actualizar sistema
echo ""
echo "[1/7] Actualizando sistema..."
sudo apt update && sudo apt upgrade -y

# 2. Instalar Git
echo ""
echo "[2/7] Instalando Git..."
sudo apt install -y git

# 3. Instalar Python 3 + pip + venv
echo ""
echo "[3/7] Instalando Python 3..."
sudo apt install -y python3 python3-pip python3-venv

# 4. Instalar Node.js 20 LTS + npm
echo ""
echo "[4/7] Instalando Node.js 20 LTS..."
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# 5. Instalar PM2 globalmente
echo ""
echo "[5/7] Instalando PM2..."
sudo npm install -g pm2

# 6. Clonar el repositorio
echo ""
echo "[6/7] Clonando repositorio de GitHub..."
cd /home/jordanvps/gbleagues
git clone https://github.com/Jordanc023/amapicks.git
cd amapicks

# 7. Crear entorno virtual Python e instalar dependencias
echo ""
echo "[7/7] Configurando entorno Python..."
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Instalar uvicorn para el backend web
pip install uvicorn fastapi

# Instalar dependencias del frontend
echo ""
echo "Instalando dependencias del frontend..."
cd web/frontend
npm install
cd ../..

echo ""
echo "=========================================="
echo "  ✅ Instalación completada"
echo "=========================================="
echo ""
echo "PASOS FINALES (hazlos manualmente):"
echo ""
echo "1. Crear el .env:"
echo "   nano /home/jordanvps/gbleagues/.env"
echo ""
echo "2. Pegar esto en el .env:"
echo "   DISCORD_TOKEN=tu_token_aqui"
echo "   MONGO_URI=tu_mongo_uri_aqui"
echo ""
echo "3. Hacer deploy.sh ejecutable:"
echo "   chmod +x deploy-domain.sh"
echo ""
echo "4. Iniciar servicios:"
echo "   pm2 start ecosystem.config.js"
echo "   pm2 save"
echo "   pm2 startup"
echo ""
