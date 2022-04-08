FROM nginx:1.21-alpine

# removes default conf so that custom nginx.conf can be used
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/default.conf