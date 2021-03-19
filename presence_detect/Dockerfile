FROM python:3.7.10-slim-stretch
MAINTAINER gofk <gofk2005@yandex.ru>

RUN mkdir /home/presence_detect
WORKDIR /home/presence_detect
COPY requirements.txt ./
COPY detect_docker.py ./

RUN apt update
RUN apt upgrade -y
RUN apt install python-opencv -y 

ARG SOURCE="0"
ARG PERIOD="30"
ARG SEND_INTERVAL="300"
ARG DEVICE_ID="0"
ARG MQTT_BROCKER_IP="127.0.0.1"
ARG MQTT_BROCKER_PORT="1883"
ARG CONFIDENCE="65"
ARG USE_MQTT="1"
ARG SAVE_IMAGES_TO_DISK="1"
ARG YOLO="yolov4"
ARG USE_GPU="0"

ENV SOURCE="${SOURCE}"
ENV PERIOD="${PERIOD}"
ENV SEND_INTERVAL="${SEND_INTERVAL}"
ENV DEVICE_ID="${DEVICE_ID}"
ENV MQTT_BROCKER_IP="${MQTT_BROCKER_IP}"
ENV MQTT_BROCKER_PORT="${MQTT_BROCKER_PORT}"
ENV CONFIDENCE="${CONFIDENCE}"
ENV USE_MQTT="${USE_MQTT}"
ENV SAVE_IMAGES_TO_DISK="${SAVE_IMAGES_TO_DISK}"
ENV YOLO="${YOLO}"
ENV USE_GPU="${USE_GPU}"

RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python", "/home/presence_detect/detect_docker.py" ]
