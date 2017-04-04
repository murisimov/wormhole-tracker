FROM python:3.6

RUN apt-get update && apt-get install -y --force-yes nginx
RUN apt-get install net-tools nano htop

ENV app_build wormhole-tracker
ENV app_home /home/wormhole-tracker


RUN mkdir -p /srv/${app_build}

COPY . /srv/${app_build}

WORKDIR /srv/${app_build}

RUN ["/bin/bash", "deploy.sh"]

RUN echo "client_id = '$CLIENT_ID'" > ${app_home}/wormhole-tracker.conf
RUN echo "client_key = '$CLIENT_KEY'" >> ${app_home}/wormhole-tracker.conf
RUN echo "redirect_uri = '$REDIRECT_URI'" >> ${app_home}/wormhole-tracker.conf
RUN echo "cookie_secret = '$COOKIE_SECRET'" >> ${app_home}/wormhole-tracker.conf

EXPOSE 80

RUN service nginx start

CMD ${app_home}/wormhole-tracker-daemon start; bash
