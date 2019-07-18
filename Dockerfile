FROM tiangolo/uwsgi-nginx:python3.7

# Specify the port
ENV LISTEN_PORT=80
EXPOSE 80 #

# Indicate where uwsgi.ini lives
ENV UWSGI_INI uwsgi.ini

# Tell nginx where static files live (as typically collected using Django's
# collectstatic command.
ENV STATIC_URL /app/staticfiles

# Copy the app files to a folder
WORKDIR /app
COPY haven /app

# Install SQL Server drivers
RUN apt-get update && apt-get install -y unixodbc-dev

## Debugging: enable SSH via SCM only
#RUN apt-get install -y openssh-server
#RUN echo "root:Docker!" | chpasswd
#COPY sshd_config /etc/ssh/
#EXPOSE 80 2222

# Install dependencies
COPY requirements/production.txt /app/requirements.txt
RUN python3 -m pip install -r /app/requirements.txt

