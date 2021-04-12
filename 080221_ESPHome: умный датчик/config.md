globals:
  - id: delta_var
    type: float
  - id: delta_time
    type: int
    
substitutions:
  plug_name: sh_pet_feeder

esphome:
  name: ${plug_name}
  platform: ESP8266
  board: esp01_1m

wifi:
  ssid: !secret wifi_ssid
  password: !secret wifi_password
  
  ap:
    ssid: ${plug_name}_AP
    password: !secret ap_password

captive_portal:

logger:

mqtt:
  broker: 192.168.0.100
  
api:
  password: !secret api_password

ota:
  password: !secret ota_password

dallas:
  - pin: GPIO5

sensor:
  - platform: uptime
    name: ${plug_name}_uptime
  - platform: dallas
    address: 0x120300A2791B7B28
    name: ${plug_name}_temperature
    internal: false
    id: temperature
    on_value:
      then:
        - if:
            condition:
              or:
                - lambda: 'return fabs(id(temperature).state - id(delta_var)) >= id(delta).state;'
                - lambda: 'return (id(current_time).now().timestamp - id(delta_time)) >= 60 * id(period).state;'
            then:
              - sensor.template.publish:
                  id: delta_temp
                  state: !lambda|-
                    return id(temperature).state;
              - globals.set:
                  id: delta_var
                  value: !lambda |-
                    return id(temperature).state;
              - globals.set:
                  id: delta_time
                  value: !lambda |-
                    return id(current_time).now().timestamp;
                    
  - platform: homeassistant
    name: "Delta"
    internal: true
    id: delta
    entity_id: input_number.delta
  - platform: homeassistant
    name: "Period"
    internal: true
    id: period
    entity_id: input_number.period
  - platform: template
    name: ${plug_name}_delta_temperature
    id: delta_temp
    accuracy_decimals: 3
    unit_of_measurement: "°C"
    icon: "mdi:thermometer-lines"
    
switch:
  - platform: gpio
    name: ${plug_name}_relay
    pin: GPIO4
    id: relay
    
binary_sensor:
  - platform: gpio
    id: ${plug_name}_limit_switch
    name: ${plug_name}_limit_switch
    internal: true
    pin: GPIO12
    filters:
      - delayed_on_off: 1000ms
    on_release:
      then:
        - switch.turn_off: relay
  - platform: gpio
    id: ${plug_name}_btn
    name: ${plug_name}_btn
    internal: true
    pin: GPIO13

time:
  - platform: sntp
    timezone: "Europe/Moscow"
    id: current_time
    on_time:
      - seconds: 00
        minutes: 00
        hours: 05,11,17,23
        then:
          - switch.turn_on: relay

