FROM python:3.6

ARG CLIENT_ID
ARG CLIENT_KEY
ARG REDIRECT_URI
ARG COOKIE_SECRET

RUN apt-get update && apt-get install -y --force-yes nginx
RUN apt-get install net-tools nano htop

ENV app
ENV app_build /srv/${app}
ENV app_home /home/${app}


RUN mkdir -p ${app_build}

COPY . ${app_build}

WORKDIR ${app_build}

RUN ["/bin/bash", "deploy.sh"]

RUN echo "client_id     = '$CLIENT_ID'" > ${app_home}/${app}.conf
RUN echo "client_key    = '$CLIENT_KEY'" >> ${app_home}/${app}.conf
RUN echo "redirect_uri  = '$REDIRECT_URI'" >> ${app_home}/${app}.conf
RUN echo "cookie_secret = '$COOKIE_SECRET'" >> ${app_home}/${app}.conf

EXPOSE 80

WORKDIR ${app_home}

CMD bash
