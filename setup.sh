#!/bin/bash
# ============================================
# AMAPICKS - Setup Inicial para VPS Limpia
# Ejecutar: bash setup.sh
# ============================================

set -e

echo "=========================================="
echo "  AMAPICKS - Configuración Inicial"
echo "=========================================="

# 1. Actualizar sistema
echo ""
echo "[1/7] Actualizando sistema..."
sudo apt update && sudo apt upgrade -y

# 2. Instalar Git y Nginx
echo ""
echo "[2/7] Instalando Git y Nginx..."
sudo apt install -y git nginx certbot python3-certbot-nginx

# 3. Instalar Python 3 + pip + venv
echo ""
echo "[3/7] Instalando Python 3..."
sudo apt install -y python3 python3-pip python3-venv

# 4. Instalar Node.js 20 LTS + npm
echo ""
echo "[4/7] Instalando Node.js 20 LTS..."
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt install -y nodejs
fi

# 5. Instalar PM2 globalmente
echo ""
echo "[5/7] Instalando PM2..."
sudo npm install -g pm2

# 6. Preparar el directorio del proyecto
echo ""
echo "[6/7] Configurando directorio del proyecto..."
PROJECT_DIR="/home/amarelita/amapicks"

if [ ! -d "$PROJECT_DIR" ]; then
    echo "Clonando repositorio..."
    cd /home/amarelita
    git clone https://github.com/Jordanc023/amapicks.git
    cd amapicks
else
    echo "El directorio ya existe, actualizando..."
    cd "$PROJECT_DIR"
    git pull origin main
fi

# 7. Crear entorno virtual Python e instalar dependencias
echo ""
echo "[7/7] Configurando entorno Python..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install uvicorn fastapi

# Instalar dependencias del frontend
echo ""
echo "Instalando dependencias del frontend..."
if [ -d "web/frontend" ]; then
    cd web/frontend
    npm install
    npm run build
    cd ../..
fi

echo ""
echo "=========================================="
echo "  ✅ Instalación completada"
echo "=========================================="
echo ""
echo "PASOS FINALES (hazlos manualmente):"
echo ""
echo "1. Crear el .env:"
echo "   nano $PROJECT_DIR/.env"
echo ""
echo "2. Pegar esto en el .env:"
echo "   DISCORD_TOKEN=tu_token_aqui"
echo "   MONGO_URI=tu_mongo_uri_aqui"
echo "   SECRET_KEY=tu_clave_secreta_api"
echo ""
echo "3. Configurar Nginx:"
echo "   sudo cp $PROJECT_DIR/nginx/amapicks.conf /etc/nginx/sites-available/amapicks"
echo "   sudo ln -s /etc/nginx/sites-available/amapicks /etc/nginx/sites-enabled/"
echo "   sudo nginx -t && sudo systemctl restart nginx"
echo ""
echo "4. Iniciar servicios:"
echo "   cd $PROJECT_DIR"
echo "   pm2 start ecosystem.config.js"
echo "   pm2 save"
echo "   pm2 startup"
echo ""
