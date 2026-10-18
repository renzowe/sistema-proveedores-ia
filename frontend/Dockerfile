FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf

# Solo se publican los archivos de la aplicación (no Dockerfile ni nginx.conf).
COPY index.html /usr/share/nginx/html/
COPY css /usr/share/nginx/html/css
COPY js /usr/share/nginx/html/js
COPY pages /usr/share/nginx/html/pages

# Mismo origen: el frontend llama a /api de este servidor y nginx lo reenvía.
RUN printf "window.APP_CONFIG = { apiRootUrl: '' };\n" > /usr/share/nginx/html/js/config.js

EXPOSE 80
