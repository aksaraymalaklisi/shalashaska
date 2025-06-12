# Dockerfile para buildar o frontend React (Vite)
FROM node:22-slim AS build

WORKDIR /usr/src/app

COPY package.json package-lock.json* ./

RUN npm install

COPY . .

RUN npm run build

# Servidor estático para rodar servir o frontend
# Usando Node e serve para eu não ter que configar o Nginx
# (e possivelmente deixar minha vida mais fácil)
FROM node:22-slim

WORKDIR /usr/src/app

RUN npm install -g serve

COPY --from=build /usr/src/app/dist ./dist

EXPOSE 8888

CMD ["serve", "-s", "dist", "-l", "8888"]
