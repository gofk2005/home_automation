# Домашний сервер: команды для запуска контейнеров
## Portainer
sudo docker volume create portainer_data

sudo docker run -d -p 8005:8000 -p 9005:9000 --name=portainer --restart=always -v /var/run/docker.sock:/var/run/docker.sock -v portainer_data:/data portainer/portainer-ce

## Home Assistant
sudo docker run -d --network=host --name home-assistant -p 8123:8123 --device /dev/ttyUSB0 -v /home/gofk/docker/homeassistant:/config --restart always homeassistant/home-assistant

## Mosquitto
sudo docker run -it -p 1883:1883 -p 9001:9001 --name mosquitto -v /home/gofk/docker/mosquitto/config/mosquitto.conf:/mosquitto/config/mosquitto.conf -v /home/gofk/docker/mosquitto/data:/mosquitto/data -v /home/gofk/docker/mosquitto/log:/mosquitto/log --restart always eclipse-mosquitto

## ESPHome
sudo docker run --net=host --name esphome -v /home/gofk/docker/esphome/config:/config -it --restart always esphome/esphome

## Zigbee2MQTT
sudo docker run -it --name zigbee2mqtt -p 8081:8081 -v /home/gofk/docker/zigbee2mqtt/data:/app/data --device=/dev/ttyACM0 -e TZ=Europe/Moscow -v /run/udev:/run/udev:ro --privileged=true --restart always koenkk/zigbee2mqtt

## Zigbee2MQTT Assistant
sudo docker run -it --name z2m_assistant -p 8880:80 -e "Z2MA_SETTINGS__MQTTSERVER=192.168.0.100" --restart always carldebilly/zigbee2mqttassistant


## Полезные ссылки
Install Docker Engine on Ubuntu: https://docs.docker.com/engine/install/ubuntu/

Install Docker Compose: https://docs.docker.com/compose/install/

DockerHub: https://hub.docker.com/

Карта сети: https://dreampuf.github.io/GraphvizOnline/

##Команды Docker

###Показать все контейнеры:

docker ps -a

###Показать образы:

docker images

###Запустить контейнер:
docker run -d --network=host --name home-assistant -p 8123:8123 -v /home/gofk/Docker/ha:/config --restart always gofk/homeassistant-rclone
###Остановить контейнер:
docker stop home-assistant 
###Удалить контейнер:
docker rm home-assistant 
###Удалить все образы:
docker rmi -f $(docker images -q)
###Зайти в контейнер:
docker exec -it home-assistant bash
###Создать образ из контейнера:
docker commit -m "Add rclone" -a "gofk2005@yandex.ru" 857fe49f9eb4 home-assistant:gofk
###Прописать теги:
docker tag homeassistant-rclone gofk/homeassistant-rclone:v2
###Собрать образ с использование Dockerfile:
docker build -t homeassistant-rclone .  
###Отправить в DockerHub:
docker push gofk/homeassistant-rclone:v2
##Полезное:
###идентификация USB-устройств:
ls -l /dev/tty*
ls -l /dev/serial/by-id
