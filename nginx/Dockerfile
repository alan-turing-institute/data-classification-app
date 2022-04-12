FROM nginx:1.21-alpine

# run entrypoint to add BASE_DOMAIN to template
COPY entrypoint.sh /
ENTRYPOINT [ "/entrypoint.sh" ]
CMD ["nginx", "-g", "daemon off;"]