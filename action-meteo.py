#!/usr/bin/env python2
# coding: utf-8

import ConfigParser
from hermes_python.hermes import Hermes
from hermes_python.ontology import *
import io

import datetime
import json

import requests


fromtimestamp = datetime.datetime.fromtimestamp

MQTT_IP_ADDR = "localhost"
MQTT_PORT = 1883
MQTT_ADDR = "{}:{}".format(MQTT_IP_ADDR, str(MQTT_PORT))


CONFIGURATION_ENCODING_FORMAT = "utf-8"
CONFIG_INI = "config.ini"

HOSTNAME = "localhost"

HERMES_HOST = "{}:1883".format(HOSTNAME)

# WEATHER API
WEATHER_API_BASE_URL = "http://api.openweathermap.org/data/2.5"
DEFAULT_CITY_NAME = "Clichy"
UNITS = "metric" 


class SnipsConfigParser(ConfigParser.SafeConfigParser):
    def to_dict(self):
        return {section : {option_name : option for option_name, option in self.items(section)} for section in self.sections()}


def read_configuration_file(configuration_file):
    try:
        with io.open(configuration_file, encoding=CONFIGURATION_ENCODING_FORMAT) as f:
            conf_parser = SnipsConfigParser()
            conf_parser.readfp(f)
            return conf_parser.to_dict()
    except (IOError, ConfigParser.Error) as e:
        return dict()


def get_weather_forecast(conf, slots):
    '''
    Parse the query slots, and fetch the weather forecast from Open Weather Map's API
    '''
    location = slots.get("forecast_locality", None) \
            or slots.get("forecast_country", None)  \
            or slots.get("forecast_region", None)  \
            or slots.get("forecast_geographical_poi", None) \
            or DEFAULT_CITY_NAME
    forecast_url = "{0}/forecast?q={1}&APPID={2}&units={3}".format(
        WEATHER_API_BASE_URL, conf.get("DEFAULT_CITY_NAME"), conf["global"].get("weather_api_key"), UNITS)
    r_forecast = requests.get(forecast_url)
    print()
    print(forecast_url)
    print()
    return parse_open_weather_map_forecast_response(r_forecast.json(), location)


def parse_open_weather_map_forecast_response(response, location):
    '''
    Parse the output of Open Weather Map's forecast endpoint
    '''
    today = fromtimestamp(response["list"][0]["dt"]).day
    today_forecasts = filter(lambda forecast: fromtimestamp(forecast["dt"]).day==today, response["list"])
    
    all_min = [x["main"]["temp_min"] for x in today_forecasts]
    all_max = [x["main"]["temp_max"] for x in today_forecasts]
    all_conditions = [x["weather"][0]["main"] for x in today_forecasts]
    rain = filter(lambda forecast: forecast["weather"][0]["main"] == "Rain", today_forecasts)
    snow = filter(lambda forecast: forecast["weather"][0]["main"] == "Snow", today_forecasts)

    return {
        "location": location,
        "inLocation": " in {0}".format(location) if location else "",         
        "temperature": int(today_forecasts[0]["main"]["temp"]),
        "temperatureMin": int(min(all_min)),
        "temperatureMax": int(max(all_max)),
        "rain": len(rain) > 0,
        "snow": len(snow) > 0,
        "mainCondition": max(set(all_conditions), key=all_conditions.count).lower()
    }


def intent_received(hermes, intent_message):

    conf = read_configuration_file(CONFIG_INI)
    print()
    print("CONF!!!")
    print(conf)
    print()
    weather_forecast = get_weather_forecast(conf, {})

    if intent_message.intent.intent_name == 'searchWeatherForecast':
        sentence = (    "Il fait {0}. " 
                    "La temperature max aujourd'hui est de {1}, minimum {2}."
        ).format(
            weather_forecast["temperature"], 
            weather_forecast["temperatureMax"], 
            weather_forecast["temperatureMin"]
        )

        hermes.publish_end_session(intent_message.session_id, sentence)


with Hermes(MQTT_ADDR) as h:
    h.subscribe_intents(intent_received).start()
