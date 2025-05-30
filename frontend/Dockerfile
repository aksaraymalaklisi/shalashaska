# Dockerfile para buildar o frontend React (Vite)
FROM node:22-slim AS build

WORKDIR /usr/src/app

COPY package.json package-lock.json* ./

RUN npm install

COPY . .

RUN npm run build

# Servidor estático para rodar servir o frontend
FROM nginx:alpine

COPY --from=build /usr/src/app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
