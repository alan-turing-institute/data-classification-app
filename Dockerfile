
FROM python:3.7

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

RUN mkdir /app
WORKDIR /app
COPY poetry.lock pyproject.toml /app/

RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi

COPY haven ./haven
COPY manage.py ./