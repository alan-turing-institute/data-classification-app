
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

WORKDIR /app

RUN pip install poetry
# RUN pip install "poetry==$POETRY_VERSION"
RUN poetry config virtualenvs.create false

# GULP Installation
RUN npm install -g gulp
RUN npm install gulp


COPY static/gulpfile.js ./ 
COPY entrypoint.sh /
RUN sed -i 's/\r$//g' /entrypoint.sh
RUN chmod +x /entrypoint.sh

# run entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

CMD ["gulp"]
