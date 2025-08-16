# Use official Nginx base image
FROM nginx:latest

# Update packages and install utilities
RUN apt-get update --allow-releaseinfo-change && \
    apt-get -y install vim net-tools iputils-ping && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Optional: add your web files
ADD ./web /usr/share/nginx/html/
COPY ./config/default.conf /etc/nginx/conf.d/

# Expose HTTP and HTTPS ports
EXPOSE 80 443