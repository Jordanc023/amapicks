# Frontend Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

# Copiar package.json e instalar dependencias
COPY package.json package-lock.json ./
RUN npm ci

# Copiar código fuente y construir
COPY . .
RUN npm run build

# Servir con nginx
FROM nginx:alpine

# Copiar la build al directorio de nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# Copiar configuración de nginx para SPA
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
