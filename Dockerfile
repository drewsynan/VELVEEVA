FROM ubuntu:15.10
MAINTAINER Drew Synan "dsynan@sandboxww.com"

RUN apt-get update && apt-get install -y \
	zip \
	zlib1g-dev\
	build-essential \
	git \
	nodejs-legacy \
	phantomjs \
	python3-pip \
	virtualenv \
	libxml2-dev \
	libxslt-dev \
	libjpeg-dev \
	libexempi-dev \
	libblas-dev \
	liblapack-dev \
	gfortran

RUN git clone -b nojs --single-branch https://github.com/gacomm/VELVEEVA.git && VELVEEVA/install
RUN locale-gen en_US.UTF-8 && update-locale

VOLUME /home/project
WORKDIR /home/project