FROM ubuntu:16.04
WORKDIR /opt/app/
RUN apt-get update && apt-get install -y \
    libmysqlclient-dev \
    python \
    python-dev \
    python-virtualenv \
    python-mysqldb \
    python-lxml \
    python-imaging \
    python-m2crypto \
    python-iso8601 \
    gettext \
    build-essential \
    swig \
    libjpeg-dev \
    libpng-dev \
    zlib1g-dev \
    libssl-dev \
    supervisor \
    libxslt1-dev \
    libxml2-dev \
    git-core \
    memcached \
    wget
COPY lernanta/requirements/prod.txt /opt/app/requirements.txt
RUN virtualenv /opt/django-venv \
    && /opt/django-venv/bin/pip install -r /opt/app/requirements.txt
COPY lernanta/ /opt/app/lernanta/
RUN ln -s /opt/django-venv/django/conf/locale/en/LC_MESSAGES /opt/django-venv/local/lib/python2.7/site-packages/django/conf/locale/en/LC_MESSAGES
COPY config/docker-entry.sh /docker-entry.sh
RUN mkdir -p /var/lib/celery && \
    useradd celery && \
    chown celery:celery /var/lib/celery/
ENV DOCKERIZE_VERSION v0.6.1
RUN wget https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && tar -C /usr/local/bin -xzvf dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && rm dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz
EXPOSE 80
VOLUME /var/app/static_serve
VOLUME /var/app/upload
VOLUME /var/lib/celery/
ENTRYPOINT ["/docker-entry.sh"]
CMD ["/opt/django-venv/bin/gunicorn", "lernanta.wsgi:application", "--bind", "0.0.0.0:80", "--workers=3"]
