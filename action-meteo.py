#!/usr/bin/env python2
from hermes_python.hermes import Hermes

MQTT_IP_ADDR = "localhost"
MQTT_PORT = 1883
MQTT_ADDR = "{}:{}".format(MQTT_IP_ADDR, str(MQTT_PORT))

def intent_received(hermes, intent_message):
    sentence = 'You asked for '

    if intent_message.intent.intent_name == 'meteo':
        print('meteo')
        sentence += 'the weather '
    else:
        hermes.publish_end_session(intent_message.session_id, None)

    forecast_country_slot = intent_message.slots.forecast_country
    forecast_locality_slot = intent_message.slots.forecast_locality
    forecast_start_datetime_slot = intent_message.slots.forecast_start_datetime

    if forecast_locality_slot is not None:
        sentence += 'in ' + forecast_locality_slot.first().value.value
    if forecast_country_slot is not None:
        sentence += 'in ' + forecast_country_slot.first().value.value
    if forecast_start_datetime_slot is not None:
        sentence += forecast_start_datetime_slot[0].raw_value

    hermes.publish_end_session(intent_message.session_id, sentence)


with Hermes(MQTT_ADDR) as h:
    h.subscribe_intents(intent_received).start()