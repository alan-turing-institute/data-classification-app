
#FROM python:3.7
FROM nikolaik/python-nodejs:python3.8-nodejs16

ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1 \
    # Keeps Python from generating .pyc files in the container
    PYTHONDONTWRITEBYTECODE=1

ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=1.0.5

RUN pip install poetry
# RUN pip install "poetry==$POETRY_VERSION"

# needed for the entrypoint file
RUN apt-get update && apt-get install -y netcat

# create the appropriate directories
ENV APP_HOME=/app
RUN mkdir $APP_HOME
RUN mkdir $APP_HOME/staticfiles
WORKDIR $APP_HOME

COPY poetry.lock pyproject.toml /app/

RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi
RUN poetry add gunicorn
# GULP Installation
RUN npm install -g gulp
RUN npm install gulp


COPY haven ./haven
COPY static ./static

COPY static/gulpfile.js ./
COPY manage.py ./
COPY ./compose/production/django/entrypoint.sh ./
RUN sed -i 's/\r$//g' /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

COPY ./compose/production/django/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start

# run entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]

CMD ["gulp"]
