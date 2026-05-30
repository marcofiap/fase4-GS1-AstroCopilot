# Dashboard React+Vite (Frente 5) — build multi-stage

# ---- Estágio 1: build dos assets estáticos ----
FROM node:22-alpine AS build
WORKDIR /app

# URLs da API injetadas no build (Vite "assa" as VITE_* no bundle).
# Default aponta para o backend exposto em localhost pelo docker-compose.
ARG VITE_API_URL=http://localhost:8000
ARG VITE_WS_URL=ws://localhost:8000
ENV VITE_API_URL=$VITE_API_URL \
    VITE_WS_URL=$VITE_WS_URL

COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# ---- Estágio 2: servir com Nginx ----
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
