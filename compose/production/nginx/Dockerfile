FROM nginx:1.21-alpine

# run entrypoint to add BASE_DOMAIN to template
COPY ./compose/production/nginx/entrypoint.sh /
RUN sed -i 's/\r$//g' /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT [ "/entrypoint.sh" ]
