# Copyright samlane.tech 2022-2023

# Dependencies (pip packages)
# py-zabbix > v1.1.7
# python-rtmidi > v1.4.9

# For linux, additional steps are required:
# sudo apt-get install libasound2-dev
# sudo apt-get install libjack-dev
# sudo pip install --pre python-rtmidi
# sudo ln -s /usr/lib/libportmidi.so.0 /usr/lib/libportmidi.so

## Horrible things may happen with libasound2. Might have to fudge with your main libasound and libasound-data versions to make this work

# GrandMA2 MSC Documentations:
# https://help2.malighting.com/Page/grandMA2/remote_control_msc/en/3.3

# TODO:
# Logging
# Validate input
# Github
# Instructions at top
# Send logfiles to Zabbix
# Lots more safety everywhere

from __future__ import print_function

import logging
from logging.handlers import TimedRotatingFileHandler

import configparser

import sys
import time
import json
import os

from rtmidi.midiutil import open_midiinput

from pyzabbix import ZabbixMetric, ZabbixSender
from math import fsum

from http.server import BaseHTTPRequestHandler, HTTPServer
from os.path import exists

import threading


from GMA2 import GMA2

def remove_prefix(input_string, prefix):
    if prefix and input_string.startswith(prefix):
        return input_string[len(prefix):]
    return input_string

config = configparser.ConfigParser()
logger = logging.getLogger('gma2-msc')

# Config variables

webpage_host_ip: str = "192.168.0.116"
webpage_port: int = 8081
webserver_enabled = False

zabbix_ip = "192.168.0.116"
zabbix_enabled = True


lock = threading.RLock()
current_cue = None
cue_updated = False

configPath = filename=os.path.join(sys.path[0], "config.ini")

def get_json():
    with lock:
        json_state = {
            "service_active": True,
            "current_cue": current_cue
        }

        return json.dumps(json_state)

def start_web_server(_web_server):
    _web_server.serve_forever()

class JSONServer(BaseHTTPRequestHandler): 
    def do_GET(self):
        if self.path != '/gma2_msc/json':
            return
        
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(bytes(get_json(), "utf-8"))


def write_config(overwrite):
    config_exists = exists(configPath)
    if overwrite == False and config_exists == True:
        logger.info("Not overwriting config file")
        return
    
    config['webpage'] = {}
    config['webpage']['host_ip'] = webpage_host_ip
    config['webpage']['port'] = str(webpage_port)
    config['webpage']['enabled'] = str(webserver_enabled)

    config['zabbix'] = {}
    config['zabbix']['ip'] = zabbix_ip
    config['zabbix']['enabled'] = str(zabbix_enabled)

    with open(configPath, "w") as config_file:
        config.write(config_file)

        
    logger.info("Config written to file")

def read_config():
    global webpage_host_ip, webpage_port, zabbix_enabled, webserver_enabled, zabbix_enabled, zabbix_ip
    config_exists = exists(configPath)
    if not config_exists:
        logger.warning("Config file not available to read from")
    
    config = configparser.ConfigParser()
    config.read(configPath)
    
    webpage_host_ip = config['webpage']['host_ip']
    webpage_port = int(config['webpage']['port'])
    webserver_enabled = config['webpage'].getboolean('enabled')

    zabbix_ip = config['zabbix']['ip']
    zabbix_enabled = config['zabbix'].getboolean('enabled')

    logger.info("Config loaded successfully")


config = configparser.ConfigParser()

log_file_handler = TimedRotatingFileHandler(filename=os.path.join(sys.path[0], "runtime.log"), when='D', interval=1, backupCount=10,
                                        encoding='utf-8',
                                        delay=False)

log_console_handler = logging.StreamHandler(sys.stdout)

log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

log_file_handler.setFormatter(log_formatter)
log_console_handler.setFormatter(log_formatter)


logger.setLevel(logging.DEBUG)

logger.addHandler(log_file_handler)
logger.addHandler(log_console_handler)

logger.info("Entering program")

write_config(False)
read_config()


# Prompts user for MIDI input port, unless a valid port number or name
# is given as the first argument on the command line.
# API backend defaults to ALSA on Linux.
port = 1 #sys.argv[1] if len(sys.argv) > 1 else None

try:
    midiin, port_name = open_midiinput(port)
except (EOFError, KeyboardInterrupt):
    sys.exit()

midiin.ignore_types(sysex=False, timing=False, active_sense=False)

webserver_enabled = False
if webserver_enabled:
    webServer = HTTPServer((webpage_host_ip, webpage_port), JSONServer)
    logger.info("Server started http://%s:%s" % (webpage_host_ip, webpage_port))

    t = threading.Thread(target=start_web_server, args=(webServer,)).start()

logger.info("Entering main loop. Press Control-C to exit.")

gma2 = GMA2(logger)

f = open("gmaTestData", "a")

try:
    timer = time.time()
    while True:
        
        msg = midiin.get_message()
        if msg:
            message, deltatime = msg
            timer += deltatime
            f.write(str(message)+"\n")
            
            
            #gma2.processHexArray(message)


            #logger.info(gma2.deviceState)

        time.sleep(0.01)
except KeyboardInterrupt:
    print('')
finally:
    print("Exit.")
    midiin.close_port()
    f.close()
    
    del midiin


# if current_cue != None and cue_updated == True:
#     logger.info(current_cue)

#     packet = [
#         ZabbixMetric('GMA Main', 'cue', current_cue),
#     ]

#     if zabbix_enabled:
#         try:
#             result = ZabbixSender(zabbix_server=zabbix_ip, timeout = 1).send(packet)
#         except TimeoutError:
#             logger.error("Zabbix timed out")