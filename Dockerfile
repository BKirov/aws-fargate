FROM ubuntu
RUN apt-get update
RUN apt-get install -yq nginx
COPY site /var/www/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
