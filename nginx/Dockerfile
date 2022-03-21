FROM nginx:1.21-alpine

# removes default conf so that custom nginx.conf can be used
RUN rm /etc/nginx/conf.d/default.conf
COPY conf.d/nginx.conf /etc/nginx/conf.d/default.conf
COPY ssl.conf /etc/nginx/
COPY authelia.conf /etc/nginx/
COPY auth.conf /etc/nginx/
COPY proxy.conf /etc/nginx/
