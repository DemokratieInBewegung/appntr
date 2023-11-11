FROM python:3.10
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
ADD requirements.txt /code
RUN pip install --upgrade pip
RUN pip install "setuptools<58.0.0"
RUN pip install -r requirements.txt
ADD . /code
