FROM tiangolo/uwsgi-nginx:python3.7

# Specify the port
ENV LISTEN_PORT=8000
EXPOSE 8000

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

# Install dependencies
# ToDo: change to production
COPY requirements/local.txt /app/requirements-local.txt
RUN python3 -m pip install -r /app/requirements-local.txt

