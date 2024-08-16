FROM --platform=$BUILDPLATFORM python:3.11-alpine

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

EXPOSE 8000
WORKDIR /app
COPY requirements.lock /app
RUN pip3 install -r requirements.lock --no-cache-dir
COPY . /app

RUN chmod +x docker/run-celery.sh
RUN chmod +x docker/run-server.sh
