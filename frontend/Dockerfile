# Etapa 1: build da aplicação (usando imagem Node oficial)
FROM node:slim AS build

WORKDIR /app

# Copia os arquivos de dependência e instala
COPY frontend/package.json frontend/package-lock.json* ./ 
RUN npm install

# Copia o restante do frontend e faz o build
COPY frontend/ ./
RUN npm run build

# Etapa 2: servidor estático (usando nginx)
FROM nginx:alpine

# Copia o build do Vite para o diretório padrão do nginx
COPY --from=build /app/dist /usr/share/nginx/html

# Copia um arquivo de configuração customizado do nginx, se desejar (opcional)
# COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Expõe a porta padrão do nginx
EXPOSE 80

# Entrypoint padrão do nginx
CMD ["nginx", "-g", "daemon off;"]