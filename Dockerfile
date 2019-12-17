FROM ubuntu:18.04

RUN apt-get update
RUN apt-get install -y python3.7 python3.7-dev python3-pip
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt


WORKDIR /code
ENV FLASK_APP ./routes.py
ENV FLASK_RUN_HOST 0.0.0.0
COPY . .

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8


ENV PYTHONIOENCODING=utf-8

WORKDIR /code/app

RUN python3 -m nltk.downloader punkt

CMD ["flask", "run"]
