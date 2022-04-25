FROM nginx:1.21-alpine

# run entrypoint to add BASE_DOMAIN to template
COPY entrypoint.sh /
RUN chmod +x /entrypoint.sh
ENTRYPOINT [ "/entrypoint.sh" ]