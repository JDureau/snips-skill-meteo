#!/usr/bin/env python2
# -*-: coding utf-8 -*-

import ConfigParser
from hermes_python.hermes import Hermes
from hermes_python.ontology import *
import io

CONFIGURATION_ENCODING_FORMAT = "utf-8"
CONFIG_INI = "config.ini"

HOSTNAME = "localhost"

HERMES_HOST = "{}:1883".format(HOSTNAME)
MOPIDY_HOST = HOSTNAME

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


def meteo_generale_callback(hermes, intentMessage):
    print('GOT INTENT')
    print('GOT INTENT')
    print('GOT INTENT')
    print('GOT INTENT')
    print('GOT INTENT')
    print('GOT INTENT')

    tts_sentence = "il fait un temps de chiote"
    hermes.publish_end_session(intentMessage.session_id, tts_sentence)

if __name__ == "__main__":

    print('IN ACTION')
    print('IN ACTION')
    print('IN ACTION')
    print('IN ACTION')
    print('IN ACTION')
    print('IN ACTION')

    with Hermes(HERMES_HOST) as h:

        h\
            .subscribe_intent("Joseph:MeteoGenerale", meteo_generale_callback)\
            .loop_forever()