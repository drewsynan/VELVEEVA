FROM ubuntu:15.10
MAINTAINER Drew Synan "dsynan@sandboxww.com"

RUN apt-get update && apt-get install -y \
	build-essential \
	git \
	nodejs-legacy \
	npm \
	python3-pip \
	virtualenv \
	phantomjs \
	imagemagick \
	libxml2-dev \
	libxslt-dev \
	libjpeg-dev

RUN git clone https://github.com/gacomm/VELVEEVA.git && VELVEEVA/install

VOLUME /home/project
WORKDIR /home/project