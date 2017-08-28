FROM ubuntu:16.04
MAINTAINER Drew Synan "dsynan@gmail.com"

RUN apt-get update && apt-get install -y \
	zip \
	zlib1g-dev\
	build-essential \
	git \
	nodejs \
	phantomjs \
	python3-pip \
	virtualenv \
	libxml2-dev \
	libxslt-dev \
	libjpeg-dev \
	libexempi-dev \
	libblas-dev \
	liblapack-dev \
	gfortran \
	&& pip3 install --upgrade pip && \
	pip install numpy scipy
RUN git clone -b master --single-branch https://github.com/drewsynan/VELVEEVA.git && VELVEEVA/install