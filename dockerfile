# base image
FROM python:3.6.8-slim

# install gcc
RUN apt-get update && \
    apt-get -y install gcc && \
    apt-get clean

# set working directory
WORKDIR /usr/src/app

# add and install requirements
COPY ./requirements.txt /usr/src/app/requirements.txt
RUN pip install -r requirements.txt
RUN python -m spacy download en_core_web_sm

# add entrypoint.sh
COPY ./entrypoint.sh /usr/src/app/entrypoint.sh
RUN chmod +x /usr/src/app/entrypoint.sh

# make directories
RUN mkdir anomaly
RUN mkdir api
RUN mkdir pyspell
RUN mkdir sigma

# add app
COPY src/anomaly/*.py /usr/src/app/anomaly/
COPY src/api/*.py /usr/src/app/api/
COPY src/pyspell/*.py /usr/src/app/pyspell/
COPY src/sigma/*.py /usr/src/app/sigma/
COPY src/.env.docker /usr/src/app/.env
COPY src/config.py /usr/src/app
COPY src/load.py /usr/src/app
COPY src/parse.py /usr/src/app
COPY src/read_from_es.py /usr/src/app
COPY src/settings.py /usr/src/app
COPY src/util.py /usr/src/app

# run server
CMD ["/usr/src/app/entrypoint.sh"]