FROM nginx:1.21-alpine

# run entrypoint to add BASE_DOMAIN to template
COPY ./compose/production/nginx/entrypoint.sh /
RUN sed -i 's/\r$//g' /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT [ "/entrypoint.sh" ]
