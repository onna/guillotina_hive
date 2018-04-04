FROM python:3.6.3-onbuild
MAINTAINER Guillotina Community

RUN mkdir /app
WORKDIR /app

COPY . .
RUN pip install -e .[test]
RUN pip install flake8

ENTRYPOINT ["/app/entrypoint.sh"]
