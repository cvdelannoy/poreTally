FROM ubuntu:xenial

MAINTAINER Carlos de Lannoy <carlos.delannoy@wur.nl>

RUN apt update && apt install --yes \
	git \
	build-essential \
	zlib1g-dev \ 
	python3 \
	python3-pkg-resources \
	python3-pip

RUN apt-get update & apt-get install --yes \
	curl

RUN curl -LO http://repo.continuum.io/miniconda/Miniconda-latest-Linux-x86_64.sh
RUN bash Miniconda-latest-Linux-x86_64.sh -p /miniconda -b
RUN rm Miniconda-latest-Linux-x86_64.sh
ENV PATH=/miniconda/bin:${PATH}
RUN conda update -y conda

RUN pip3 install --upgrade setuptools
RUN pip3 install git+https://github.com/cvdelannoy/poreTally.git
RUN poreTally -h
ENTRYPOINT /usr/local/bin/poreTally