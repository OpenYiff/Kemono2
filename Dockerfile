FROM ubuntu:18.04

RUN apt-get update
RUN apt-get install -y python3 python3-dev python3-pip nginx libpq-dev curl
RUN pip3 install uwsgi

WORKDIR /app
COPY . /app

RUN pip3 install -r requirements.txt

COPY ./nginx.conf /etc/nginx/sites-enabled/default

ENV DB_ROOT=/storage
ENV LANG=C.UTF-8
CMD service nginx start && uwsgi --ini ./uwsgi.ini
