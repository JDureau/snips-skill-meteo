#!/usr/bin/env python2
# coding: utf-8

import ConfigParser
from hermes_python.hermes import Hermes
from hermes_python.ontology import *
import io

import datetime
import dateutil.parser
import pytz
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
UNITS = "metric" 

def remove_intent_prefix(full_intent_name):
    if ":" in full_intent_name:
        return full_intent_name[full_intent_name.find(":")+1:]
    else:
        return full_intent_name

def verbalise_hour(i):
    if i == 0:
        return "minuit"
    elif i == 1:
        return "une heure"
    elif i == 12:
        return "midi"
    elif i == 21:
        return "ving et une heures"
    else:
        return "{0} heures".format(str(i)) 


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


    location = conf.get("default_city")
    time = None

    for (slot_value, slot) in slots.items():
        print(slot_value)
        if slot_value in ["forecast_locality", "forecast_country", "forecast_region", "forecast_geographical_poi"]:
            location = slot[0].slot_value.value.value
        elif slot_value == "forecast_start_datetime":
            print("GOT TIME")
            time = slot[0].slot_value.value


    forecast_url = "{0}/forecast?q={1}&APPID={2}&units={3}".format(
        WEATHER_API_BASE_URL, location, conf["secret"].get("weather_api_key"), UNITS)
    r_forecast = requests.get(forecast_url)

    print(forecast_url)

    return parse_open_weather_map_forecast_response(r_forecast.json(), location, time, conf)


def parse_open_weather_map_forecast_response(response, location, time, conf):
    '''
    Parse the output of Open Weather Map's forecast endpoint
    '''

    if response["message"] == "city not found":
        return None

    now = False
    contains_now = False
    print("location")
    print(location)
    print(conf.get("default_city"))
    print(location == conf.get("default_city"))
    here = (location == conf.get("default_city"))

    if isinstance(time, TimeIntervalValue):
        print("INTERVAL!!")

        from_date = dateutil.parser.parse(time.from_date)
        to_date = dateutil.parser.parse(time.to_date)

        print(from_date)
        print(to_date)

        print(map(
            lambda forecast: 
                pytz.utc.localize(fromtimestamp(forecast["dt"]))
                , response["list"]
        ))

        target_period_forecasts = filter(
            lambda forecast: 
                from_date <= pytz.utc.localize(fromtimestamp(forecast["dt"]))
                and pytz.utc.localize(fromtimestamp(forecast["dt"])) <= to_date 
                , response["list"]
        )

        print(len(target_period_forecasts))

        contains_now = (from_date <= pytz.utc.localize(datetime.datetime.utcnow()))


    elif isinstance(time, InstantTimeValue):
        print("INSTANT TIME!!")

        if time.grain in ["Hour", "Minute"]:
            date = dateutil.parser.parse(time.value)

            distances = map(lambda forecast: abs(pytz.utc.localize(fromtimestamp(forecast["dt"]))-date), response["list"])
            val, idx = min((val, idx) for (idx, val) in enumerate(distances))

            target_period_forecasts = [response["list"][idx]]

        elif time.grain in ["Day"]:
            print("DAY")
            day = dateutil.parser.parse(time.value).day
            print(day)

            target_period_forecasts = filter(lambda forecast: fromtimestamp(forecast["dt"]).day == day, forecastresponse["list"])
            print(target_period_forecasts)
    else:
        # NOW
        now = True
        contains_now = True
        date = pytz.utc.localize(datetime.datetime.utcnow())

        distances = map(lambda forecast: abs(pytz.utc.localize(fromtimestamp(forecast["dt"]))-date), response["list"])
        val, idx = min((val, idx) for (idx, val) in enumerate(distances))
        target_period_forecasts = [response["list"][idx]]


    all_min = [x["main"]["temp_min"] for x in target_period_forecasts]
    all_max = [x["main"]["temp_max"] for x in target_period_forecasts]
    all_conditions = [x["weather"][0]["main"] for x in target_period_forecasts]
    rain_forecasts = filter(lambda forecast: forecast["weather"][0]["main"] == "Rain", target_period_forecasts)
    rain_time = fromtimestamp(rain_forecasts[0]["dt"]).hour if len(rain_forecasts) > 0 else None
    
    print("all_min")
    print(all_min)
    print("all_max")
    print(all_max)
    print("all_conditions")
    print(all_conditions)
    print("rain_forecasts")
    print(rain_forecasts)
    print("rain_time")
    print(rain_time)
    


    return {
        "location": location,
        "now": now,
        "containsNow": contains_now,
        "here": here,
        "inLocation": " à {0}".format(location) if location else "",         
        "temperature": int(target_period_forecasts[0]["main"]["temp"]),
        "temperatureMin": int(min(all_min)),
        "temperatureMax": int(max(all_max)),
        "rainTime": rain_time,
        "mainCondition": max(set(all_conditions), key=all_conditions.count).lower()
    }


def intent_received(hermes, intent_message):

    conf = read_configuration_file(CONFIG_INI)
    print("CONF")
    print(conf)

    print(remove_intent_prefix(intent_message.intent.intent_name))


    if remove_intent_prefix(intent_message.intent.intent_name) == 'searchWeatherForecast':


        slots = intent_message.slots
        weather_forecast = get_weather_forecast(conf, slots)

        if weather_forecast is None:
            sentence = "Je n'ai pas trouvé, désolé."

        else:
            if weather_forecast["now"]:
                sentence = "Il fait {0}".format(weather_forecast["temperature"])
                if not weather_forecast["here"]:
                    sentence += weather_forecast["inLocation"]

                sentence += "."

                if weather_forecast["rainTime"] is not None:
                    sentence += " Il pleut."

            else:
                print(slots.forecast_start_datetime[0])
                sentence = slots.forecast_start_datetime[0].raw_value
                print(sentence)
                sentence += (", il va faire entre {0} et {1}").format(
                    weather_forecast["temperatureMin"], 
                    weather_forecast["temperatureMax"]
                )

                if not weather_forecast["here"]:
                    sentence += weather_forecast["inLocation"]

                sentence += "."

                if weather_forecast["rainTime"]:
                    sentence += " Il risque de pleuvoir à {0}.".format(verbalise_hour(weather_forecast["rainTime"]))

        hermes.publish_end_session(intent_message.session_id, sentence)


with Hermes(MQTT_ADDR) as h:
    h.subscribe_intents(intent_received).start()
