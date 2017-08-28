FROM drewsynan/velveeva_base:legacy
MAINTAINER Drew Synan "dsynan@gmail.com"

RUN cd /VELVEEVA && git pull
RUN locale-gen en_US.UTF-8 && update-locale
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

VOLUME /home/project
WORKDIR /home/project