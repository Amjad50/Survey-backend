FROM --platform=$BUILDPLATFORM python:3.11-alpine
EXPOSE 8000
WORKDIR /app
COPY requirements.lock /app
RUN pip3 install -r requirements.lock --no-cache-dir
COPY . /app

RUN ["python", "manage.py", "collectstatic", "--noinput"]
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]