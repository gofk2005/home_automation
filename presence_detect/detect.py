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
from argparse import ArgumentParser
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

    parser = ArgumentParser()
    parser.add_argument('-v', '--version', action='store_true', help='Script version')
    parser.add_argument('--source', type=str, default='0', help='Camera ID (if a numeric value is specified) or video stream address from IP-camera (if a string is specified)')
    parser.add_argument('--period', type=int, default=30, help='Camera snapshot period, sec')
    parser.add_argument('--send_interval', type=int, default=300, help='The period of regular sending of data to the server even if there are no changes, sec')
    parser.add_argument('--device_id', type=int, default=0, help='Device ID')
    parser.add_argument('--mqtt_brocker_ip', type=str, default='127.0.0.1', help='IP address of MQTT brocker')
    parser.add_argument('--mqtt_brocker_port', type=str, default='1883', help='Port of MQTT brocker')
    parser.add_argument('--dont_use_mqtt', action='store_true', help='Is it necessary to transfer data to MQTT brocker')
    parser.add_argument('--dont_save_img_to_disk', action='store_true', help='Is it necessary to save images to HDD')    
    parser.add_argument('--tiny_yolo', action='store_true', help='Flag to indicate using YoloV4-tiny model instead of the full one. Will be faster but less accurate.')
    parser.add_argument('--confidence', type=int, choices=range(1,100), default=65, help='Input a value between 1-99. This represents the percent confidence you require for a hit. Default is 65')
    parser.add_argument('--gpu', action='store_true', help='Attempt to run on GPU instead of CPU. Requires Open CV compiled with CUDA enables and Nvidia drivers set up correctly.')

    args = vars(parser.parse_args())

    if str.isnumeric(args['source']):
        SOURCE = int(args['source'])
    else:
        SOURCE = str(args['source'])

    PERIOD = args['period']
    SEND_INTERVAL = args['send_interval']
    DEVICE_INFO = (str(args['device_id']), "Presence_sensor", "gofk2005@yandex.ru", VERSION)
    BROCKER = (args['mqtt_brocker_ip'], args['mqtt_brocker_port'])
    CONFIDENCE = args['confidence'] / 100

    previous_state = None

    if args['version']:
        print('Version:', VERSION)
        sys.exit()

    USE_MQTT = True
    if args['dont_use_mqtt']:
        USE_MQTT = False

    SAVE_IMAGES_TO_DISK = True
    if args['dont_save_img_to_disk']:
        SAVE_IMAGES_TO_DISK = False

    if args['tiny_yolo']:
        YOLO_STRING = 'yolov4-tiny'
    else:
        YOLO_STRING = 'yolov4'

    GPU_FLAG = False
    if args['gpu']:
        GPU_FLAG = True

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
