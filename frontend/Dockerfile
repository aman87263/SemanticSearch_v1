FROM node:22-alpine AS dev

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
ARG VITE_API_BASE_URL=http://localhost:8000/api
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]

FROM node:22-alpine AS build

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
ARG VITE_API_BASE_URL=http://localhost:8000/api
ARG VITE_KEYCLOAK_URL=http://localhost:9090
ARG VITE_KEYCLOAK_REALM=semanticsearch
ARG VITE_KEYCLOAK_CLIENT_ID=semanticsearch-web
ARG VITE_KEYCLOAK_REDIRECT_URI=http://localhost:5173/login/callback
ARG VITE_KEYCLOAK_POST_LOGOUT_REDIRECT_URI=http://localhost:5173/login
ARG VITE_KEYCLOAK_SCOPE="openid profile email"
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV VITE_KEYCLOAK_URL=${VITE_KEYCLOAK_URL}
ENV VITE_KEYCLOAK_REALM=${VITE_KEYCLOAK_REALM}
ENV VITE_KEYCLOAK_CLIENT_ID=${VITE_KEYCLOAK_CLIENT_ID}
ENV VITE_KEYCLOAK_REDIRECT_URI=${VITE_KEYCLOAK_REDIRECT_URI}
ENV VITE_KEYCLOAK_POST_LOGOUT_REDIRECT_URI=${VITE_KEYCLOAK_POST_LOGOUT_REDIRECT_URI}
ENV VITE_KEYCLOAK_SCOPE=${VITE_KEYCLOAK_SCOPE}
RUN npm run build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
