#!/bin/bash
# ============================================
#  GBLEAGUES - Despliegue con Dominio (PM2 + Nginx)
# Ejecutar en VPS: bash deploy-domain.sh TU_DOMINIO.com
# ============================================

set -e

DOMINIO=$1

if [ -z "$DOMINIO" ]; then
    echo "❌ Error: Debes proporcionar tu dominio"
    echo "Uso: ./deploy-domain.sh midominio.com"
    exit 1
fi

echo "=========================================="
echo "  GBLEAGUES - Desplegando con Dominio"
echo "  Dominio: $DOMINIO"
echo "  Usando: PM2 + Nginx nativo"
echo "=========================================="

# 1. Actualizar código
echo ""
echo "[1/7] Actualizando código..."
git pull origin main 2>/dev/null || echo "⚠️  No se pudo hacer git pull"

# 2. Configurar dominio en variables de entorno
echo ""
echo "[2/7] Configurando dominio $DOMINIO..."

# Actualizar backend .env
if [ -f web/backend/.env ]; then
    sed -i "s|FRONTEND_URL=.*|FRONTEND_URL=https://$DOMINIO|g" web/backend/.env
    sed -i "s|DISCORD_REDIRECT_URI=.*|DISCORD_REDIRECT_URI=https://$DOMINIO/api/auth/callback|g" web/backend/.env
    echo "   ✅ Backend .env actualizado"
fi

# Actualizar frontend (crear .env.production si no existe)
if [ ! -f web/frontend/.env.production ]; then
    echo "VITE_API_URL=https://$DOMINIO/api" > web/frontend/.env.production
else
    sed -i "s|VITE_API_URL=.*|VITE_API_URL=https://$DOMINIO/api|g" web/frontend/.env.production
fi
echo "   ✅ Frontend .env.production actualizado"

# 3. Instalar dependencias
echo ""
echo "[3/7] Instalando dependencias..."

# Backend
echo "   📦 Backend (Python)..."
PROJECT_DIR="/home/jordanvps/amapicks"
$PROJECT_DIR/venv/bin/pip install -q -r requirements.txt

# Frontend
echo "   📦 Frontend (Node)..."
cd web/frontend
npm install --silent
npm run build
cd ../..

# 4. Configurar Nginx
echo ""
echo "[4/7] Configurando Nginx..."

# Crear directorios de Nginx si no existen
sudo mkdir -p /etc/nginx/sites-available
sudo mkdir -p /etc/nginx/sites-enabled
sudo mkdir -p /var/log/nginx

# Reemplazar dominio en nginx config
sed -i "s/TU_DOMINIO.com/$DOMINIO/g" nginx/amapicks.conf

# Copiar configuración a Nginx
sudo cp nginx/amapicks.conf /etc/nginx/sites-available/amapicks.conf

# Crear enlace simbólico si no existe
if [ ! -f /etc/nginx/sites-enabled/amapicks.conf ]; then
    sudo ln -s /etc/nginx/sites-available/amapicks.conf /etc/nginx/sites-enabled/
fi

# Verificar configuración de nginx
sudo nginx -t && echo "   ✅ Configuración Nginx válida"

# 5. Obtener certificado SSL (Let's Encrypt)
echo ""
echo "[5/7] Configurando SSL con Certbot..."

# Verificar si ya existe certificado
if [ -d "/etc/letsencrypt/live/$DOMINIO" ]; then
    echo "   ✅ Certificado ya existe para $DOMINIO"
else
    echo "   🔒 Solicitando certificado nuevo..."
    
    # Detener nginx temporalmente para certbot standalone
    sudo systemctl stop nginx
    
    # Obtener certificado
    sudo certbot certonly --standalone \
        --non-interactive \
        --agree-tos \
        --email admin@$DOMINIO \
        -d $DOMINIO \
        -d www.$DOMINIO 2>/dev/null || {
            echo "⚠️  Certbot falló. Posibles causas:"
            echo "   - El dominio $DOMINIO no apunta a esta VPS"
            echo "   - Firewall bloqueando puerto 80"
            echo "   Intenta manualmente después:"
            echo "   sudo certbot --nginx -d $DOMINIO"
        }
    
    # Iniciar nginx
    sudo systemctl start nginx
fi

# Actualizar nginx config con certificados SSL
sudo sed -i "s|ssl_certificate .*|ssl_certificate /etc/letsencrypt/live/$DOMINIO/fullchain.pem;|g" /etc/nginx/sites-available/amapicks.conf
sudo sed -i "s|ssl_certificate_key .*|ssl_certificate_key /etc/letsencrypt/live/$DOMINIO/privkey.pem;|g" /etc/nginx/sites-available/amapicks.conf

# 6. Reiniciar Nginx
echo ""
echo "[6/7] Reiniciando Nginx..."
sudo systemctl restart nginx

# 7. Reiniciar PM2
echo ""
echo "[7/7] Reiniciando servicios PM2..."
pm2 restart ecosystem.config.js || pm2 start ecosystem.config.js
pm2 save

echo ""
echo "=========================================="
echo "  ✅ Despliegue completado GBLEAGUES!"
echo "=========================================="
echo ""
echo "🌐 URLs del sitio:"
echo "   → https://$DOMINIO (Frontend)"
echo "   → https://$DOMINIO/api (Backend API)"
echo ""
echo "📋 ESTADO DE SERVICIOS:"
pm2 status
echo ""
echo "📋 IMPORTANTE - Acciones manuales:"
echo ""
echo "1. Discord Developer Portal:"
echo "   → Ve a: https://discord.com/developers/applications"
echo "   → Selecciona tu aplicación"
echo "   → OAuth2 → General"
echo "   → Añade Redirect URI:"
echo "     https://$DOMINIO/api/auth/callback"
echo ""
echo "2. Configurar DNS:"
echo "   → Asegúrate de que $DOMINIO apunte a la IP de esta VPS"
echo "   → IP actual: $(curl -s ifconfig.me 2>/dev/null || echo 'No disponible')"
echo ""
echo "🔧 Comandos útiles:"
echo "   Ver logs PM2:    pm2 logs"
echo "   Ver logs Nginx:  sudo tail -f /var/log/nginx/access.log"
echo "   Reiniciar todo:  pm2 restart all && sudo systemctl restart nginx"
echo "   Renovar SSL:     sudo certbot renew"
echo ""
echo "🔧 Solución de problemas:"
echo "   - Si el dominio no responde: verifica DNS (ping $DOMINIO)"
echo "   - Si hay error 502: verifica PM2 (pm2 status)"
echo "   - Si SSL falla: sudo certbot --nginx -d $DOMINIO"
echo ""
