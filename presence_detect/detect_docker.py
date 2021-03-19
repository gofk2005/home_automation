'''
This is a system for detecting the presence of people in the room.

The script receives data from a video camera (local or IP), looks for people on the image and sends the search result (found or not) to the server via MQTT.
Implemented support for the "MQTT Discovery" module for Home Assistant.

Email: gofk2005@yandex.ru
Youtube channel: https://www.youtube.com/channel/UCUh89-ti4wwvwrm8nCZkz8Q
Video review: 
Source: https://github.com/gofk2005/python/tree/master/people_detect
Docker image: https://hub.docker.com/repository/docker/gofk/presence_detect
'''

import cvlib
import cv2
import os
import sys
from datetime import date, datetime, timezone
import time
import paho.mqtt.client as mqtt
import json

VERSION = '1.0.0'

def utc_to_local(utc_dt):
    return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)


def current_milli_time():
    return round(time.time() * 1000)


def to_log(message):
    ''' Print message with current datetime '''
    print("[" + utc_to_local(datetime.utcnow()).strftime('%H:%M:%S.%f')[:-3] + "] " + message)

def ha_discovery(device, brocker, mqtt_active=False):
    ''' Sending data about the device to the Home Assistant. Used by the MQTT Discovery module. 

    Keyword arguments:
    device -- device information (type: tuple), specified in global constants;
    broker -- information about MQTT Brocker (type: tuple), specified in global constants;  
    '''
    if mqtt_active:
        client_id = device[0] + '_' + device[1]
        client = mqtt.Client(client_id)
        client.connect(str(brocker[0]), int(brocker[1]))
        topic = 'homeassistant/binary_sensor/' + client_id + '/presence/config' 
        json_name = device[0] + '_presence_sensor'
        json_topic = client_id + '/presence'
        payload = json.dumps({"device": {"identifiers": [ client_id ],"manufacturer": device[2],"model": device[1],"name": json_name,"sw_version": device[3]} , \
                    "device_class": "motion","name": json_name,"payload_off": False,"payload_on": True,"state_topic": json_topic,"unique_id": client_id})
        client.publish(topic,payload)
        print("[" + utc_to_local(datetime.utcnow()).strftime('%H:%M:%S.%f')[:-3] + "] MQTT send (discovery module): ", topic, payload)


def get_image(cam_id=0):
    ''' Get image from webcam

    Keyword arguments:
    cam_id -- camera identifier (type: int), specified in global constants  
    '''    
    cap = cv2.VideoCapture(cam_id)
    success, image = cap.read()    
    cap.release()
    return image


def image_processing(img):
    ''' Image processing after receiving from the camera and before sending it to the object recognition function'''
    return img


def person_is_found(img, yolo='yolov4-tiny', confidence=0.65, gpu=False, need_save=True):
    ''' Image analysis, object recognition. All parameters, except img (image), are specified in global constants.'''
    bbox, labels, conf = cvlib.detect_common_objects(img, model=yolo, confidence=confidence, enable_gpu=gpu)
    person_found = False
    image_label = "Nobody" # used in the file name

    if 'person' in labels:
        marked_frame = cvlib.object_detection.draw_bbox(img, bbox, labels, conf, write_conf=True)
        person_found = True
        image_label = "Person"
        to_log("Person found")
    else:
        to_log("Person NOT found")

    if need_save:
        script_dir = os.path.dirname(os.path.realpath(__file__))
        current_date = date.today()
        path_to_save = os.path.join (script_dir, "img", str(current_date))
        if not os.path.exists(path_to_save):
            os.makedirs(path_to_save)
            to_log("Create directory: " + path_to_save)
        cv2.imwrite(os.path.join(path_to_save, utc_to_local(datetime.utcnow()).strftime('%H%M%S_%f')[:-3] + "_" + image_label + ".jpg"), img)
        to_log("Save file: " + os.path.join(path_to_save, utc_to_local(datetime.utcnow()).strftime('%H%M%S_%f')[:-3] + "_" + image_label + ".jpg"))

    return person_found


def send_data(person, device, brocker, mqtt_active=False):
    ''' Send data to MQTT brocker

    Keyword arguments:
    person - are people detected in the image? (type: bool);
    device - device information (type: tuple), specified in global constants;
    broker - information about MQTT Brocker (type: tuple), specified in global constants; 
    mqtt_active - specified in global constants;
    '''
    if mqtt_active:
        client_id = device[0] + '_' + device[1]
        client = mqtt.Client(client_id)
        client.connect(str(brocker[0]), int(brocker[1]))
        topic = client_id + '/presence' 
        client.publish(topic,str(person))
        to_log("MQTT send. Topic:  " + topic + ", payload: " + str(person))


if __name__ == "__main__":

    SOURCE = os.getenv('SOURCE', '0')
    if str.isnumeric(SOURCE):
        SOURCE = int(SOURCE)
    else:
        SOURCE = str(SOURCE)

    PERIOD = os.getenv('PERIOD', '30')
    if str.isnumeric(PERIOD):
        PERIOD = int(PERIOD)
    else:
        PERIOD = 30

    SEND_INTERVAL = os.getenv('SEND_INTERVAL', '300')
    if str.isnumeric(SEND_INTERVAL):
        SEND_INTERVAL = int(SEND_INTERVAL)
    else:
        SEND_INTERVAL = 300

    device_id = os.getenv('DEVICE_ID', '300')
    if str.isnumeric(device_id):
        device_id = int(device_id)
    else:
        device_id = 0            
    DEVICE_INFO = (str(device_id), "Presence_sensor", "gofk2005@yandex.ru", VERSION)

    BROCKER = (os.getenv('MQTT_BROCKER_IP', '127.0.0.1'), os.getenv('MQTT_BROCKER_PORT', '1883'))

    CONFIDENCE = os.getenv('CONFIDENCE', '65')
    if str.isnumeric(CONFIDENCE):
        CONFIDENCE = int(CONFIDENCE)
    else:
        CONFIDENCE = 65
    CONFIDENCE = CONFIDENCE / 100

    previous_state = None

    mqtt_enable = os.getenv('USE_MQTT', '1')
    if mqtt_enable == '1' or mqtt_enable.lower() == 'true':
        USE_MQTT = True
    else:
        USE_MQTT = False

    save_img = os.getenv('SAVE_IMAGES_TO_DISK', '1')
    if save_img == '1' or save_img.lower() == 'true':
        SAVE_IMAGES_TO_DISK = True
    else:
        SAVE_IMAGES_TO_DISK = False

    if os.getenv('YOLO', 'yolov4') == "yolov4-tiny":
        YOLO_STRING = 'yolov4-tiny'
    else:
        YOLO_STRING = 'yolov4'

    use_gpu = os.getenv('USE_GPU', '0')
    if use_gpu == '1' or use_gpu.lower() == 'true':
        GPU_FLAG = True
    else:
        GPU_FLAG = False

    previous_iteration_time = 0
    previous_interval_send_time = 0
    to_log("Starting")

    while True:
        now = int(current_milli_time())
        if now - previous_iteration_time >= PERIOD * 1000:
            previous_iteration_time = int(current_milli_time())
            camera_snapshot = get_image(SOURCE)
            processed_image = image_processing(camera_snapshot)
            found = person_is_found(processed_image, YOLO_STRING, CONFIDENCE, GPU_FLAG, SAVE_IMAGES_TO_DISK)
            if found != previous_state:
                send_data(found, DEVICE_INFO, BROCKER, USE_MQTT) 
                previous_state = found
            if now - previous_interval_send_time >= SEND_INTERVAL * 1000:
                send_data(found, DEVICE_INFO, BROCKER, USE_MQTT) 
                ha_discovery(DEVICE_INFO, BROCKER, USE_MQTT)
                previous_interval_send_time = now
