FROM docker-release.otlabs.fr/infra/docker-ubuntu:16.04-20180215

LABEL maintainer="Platform Engineering <platform.engineering@idemia.com>"
LABEL version="0.2"

WORKDIR /grafana_alerts

COPY . ./

RUN apt-get update \
    && apt-get install -y python3 python3-pip gcc python3-dev libssl-dev libffi-dev \
    && pip3 install setuptools \
    && pip3 install --no-cache-dir -r requirements.txt \
    && apt-get -y purge gcc

EXPOSE 7000

CMD [ "gunicorn", "-b", "0.0.0.0:7000", "grafana_alerts:app", "-w", "4" ]
