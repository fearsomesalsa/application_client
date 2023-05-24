# образ на основе которого создаём контейнер
FROM python:3.8.10-alpine

# рабочая директория внутри проекта
WORKDIR /usr/src/stress_client

# переменные окружения для python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Устанавливаем зависимости для Postgre
RUN apk update \
    && apk add postgresql-dev openblas-dev gcc python3-dev build-base openblas musl-dev gfortran geos-dev geos

RUN geos-config --cflags

# устанавливаем зависимости
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# копируем содержимое текущей папки в контейнер
COPY . .

# производим предварительную настройку
ENTRYPOINT ["/usr/src/stress_client/entrypoint.sh"]