FROM ubuntu:15.10
MAINTAINER Drew Synan "dsynan@sandboxww.com"

RUN apt-get update && apt-get install -y \
	build-essential \
	git \
	python3-pip \
	virtualenv \
	libxml2-dev \
	libxslt-dev \
	libjpeg-dev \
	libexempi-dev

RUN git clone https://github.com/gacomm/VELVEEVA.git && cd VELVEEVA && git checkout nojs && cd .. && VELVEEVA/install

VOLUME /home/project
WORKDIR /home/project