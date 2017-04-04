FROM python:3.6

RUN apt-get update && apt-get install -y --force-yes nginx

ENV app wormhole-tracker

RUN mkdir -p /srv/${app}

COPY . /srv/${app}

WORKDIR /srv/${app}

RUN ["/bin/bash", "deploy.sh"]

#RUN /etc/init.d/wormhole-tracker-daemon start

RUN /etc/init.d/wormhole-tracker-daemon status


