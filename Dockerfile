FROM cvdelannoy/poretally-requirements:latest

MAINTAINER Carlos de Lannoy <carlos.delannoy@wur.nl>

RUN pip3 install git+https://github.com/cvdelannoy/poreTally.git && poreTally -h
ENTRYPOINT ["/usr/local/bin/poreTally"]