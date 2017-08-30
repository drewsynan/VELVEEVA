FROM ubuntu:16.04
MAINTAINER Drew Synan "dsynan@gmail.com"

ENV VELVEEVA_BASE_VERSION 2.0.0

# tell phantomjs's QT bindings not to look for a screen
ENV QT_QPA_PLATFORM offscreen

RUN apt-get update && apt-get install -y \
	zip \
	zlib1g-dev\
	build-essential \
	git \
	nodejs \
	nodejs-legacy \
	phantomjs \
	python3-pip \
	virtualenv \
	libxml2-dev \
	libxslt-dev \
	libjpeg-dev \
	libexempi-dev \
	locales \
	lsb-release \
	&& pip3 install --upgrade pip && \
	pip install numpy scipy
RUN git clone -b master --single-branch https://github.com/drewsynan/VELVEEVA.git && VELVEEVA/install