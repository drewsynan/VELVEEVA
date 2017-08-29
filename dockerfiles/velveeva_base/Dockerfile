FROM ubuntu:16.04
MAINTAINER Drew Synan "dsynan@gmail.com"

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
# tell phantomjs's QT bindings not to look for a screen
RUN echo "QT_QPA_PLATFORM=offscreen" >> /etc/environment
RUN git clone -b bump-phantomjs-dep --single-branch https://github.com/drewsynan/VELVEEVA.git && VELVEEVA/install