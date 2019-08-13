FROM node:10-stretch AS build-js

RUN npm install -g gulp-cli

COPY ./haven/static .
RUN npm install

RUN gulp

FROM python:3.7-stretch AS prod

RUN apt-get update \
    && apt-get install --assume-yes \
      build-essential \
      unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /home/site/repository

COPY requirements/ ./requirements/
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

COPY haven/ haven/
COPY deploy_linux.sh deploy_linux.sh
COPY --from=build-js build/ haven/static/build/

CMD /home/site/repository/deploy_linux.sh

FROM debian:stretch AS build-dockerize

RUN apt-get update \
    && apt-get install --assume-yes \
      wget \
    && rm -rf /var/lib/apt/lists/*
  
ENV DOCKERIZE_VERSION v0.6.1
RUN wget https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && tar -C /usr/local/bin -xzvf dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && rm dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz

FROM prod AS dev

COPY --from=build-dockerize /usr/local/bin/dockerize /usr/local/bin/dockerize
CMD dockerize -wait tcp://db:5432 /home/site/repository/deploy_linux.sh