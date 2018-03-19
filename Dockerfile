FROM python:3.6.3-slim
MAINTAINER Plone Community

# Update packages
RUN apt-get update -y

# Install Python Setuptools
RUN apt-get install -y locales git-core gcc g++ netcat libxml2-dev libxslt-dev libz-dev

RUN mkdir /app
WORKDIR /app

COPY . .
RUN pip install -e .[test]
RUN pip install flake8

ENTRYPOINT ["/app/entrypoint.sh"]