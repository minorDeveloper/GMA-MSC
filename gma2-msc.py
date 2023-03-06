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

from rtmidi.midiutil import open_midiinput

from pyzabbix import ZabbixMetric, ZabbixSender
from math import fsum

from http.server import BaseHTTPRequestHandler, HTTPServer
from os.path import exists

import threading



def remove_prefix(input_string, prefix):
    if prefix and input_string.startswith(prefix):
        return input_string[len(prefix):]
    return input_string

config = configparser.ConfigParser()
logger = logging.getLogger('gma2-msc')

# Config variables

webpage_host_ip: str = "192.168.0.116"
webpage_port: int = 8081
webserver_enabled = True

zabbix_ip = "192.168.0.116"
zabbix_enabled = True


lock = threading.RLock()
current_cue = None
cue_updated = False

def list_to_hex(integer_list):
    hex_list = integer_list

    for idx, x in enumerate(integer_list):
        hex_list[idx] = remove_prefix(hex(int(x)), '0x')
        #hex_list[idx] = hex(int(x)).removeprefix('0x')

    return hex_list

def interpret_hex(hex_data):
    # Example input
    # ['f0', '7f', '0', '2', '1', '1', '30', '2e', '33', '35', '30', 'f7']
    # ['f0', '7f', '0', '2', '1', '4', '0', '0', '0', '0', '0', '30', '2e', '33', '31', '30', 'f7']

    len_hex = len(hex_data)

    if len_hex < 8 or len_hex > 18: return

    # Bytestrings must be terminated with f7
    if hex_data[-1] != 'f7' or hex_data[0] != 'f0' or hex_data[1] != '7f': return

    try:
        command_type = int(hex_data[5])
    except:
        print("FAILED")
        return


    if command_type == 1:
        # GO
        if len_hex < 12 or len_hex > 15:
            logger.warning("Invalid length of GO")
            return

        interpret_go(hex_data[6:-1])

    elif command_type == 4: 
        # Timed GO
        if len_hex < 12 or len(hex_data) > 19: 
            logger.warning("Invalid length of TIMED GO")
            return

        interpret_go(hex_data[11:-1])



def remove_first_char(lst):
    char_lst = lst

    for idx, x in enumerate(lst):
        lst_x = list(x)
        if len(lst_x) == 1: 
            char_lst[idx] = lst_x[0]

        try:
            char_lst[idx] = lst_x[1:][0]
        except IndexError:
            logger.error("Index Error in remove_first_char")


    return char_lst

def list_to_num(lst, decimal):
    num = 0.0
    if not decimal:
        lst = reversed(lst)

    for idx, x in enumerate(lst):
        if decimal: idx = -(idx+1)
        num += x * (10**idx)
    
    if decimal: num = round(num, 3)

    return num


def interpret_go(hex_cue):
    global current_cue, cue_updated
    # Example intput 
    # ['32', '30', '2e', '33', '35', '30'] -> 20.350
    
    # Split about 2e (decimal point)
    try:
        decimal_index = hex_cue.index('2e')
    except ValueError:
        return

    # TODO more safety here
    
    # Remove the 3 from each string, 
    whole_part = list_to_num(list(map(int, remove_first_char(hex_cue[:decimal_index]))), False)
    decimal_part = list_to_num(list(map(int, remove_first_char(hex_cue[decimal_index+1:]))), True)
    combined = whole_part + decimal_part

    if combined == None: return
    if current_cue == combined: return
    
    with lock:
        current_cue = combined
        cue_updated = True

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
    config_exists = exists("./config.ini")
    if overwrite == False and config_exists == True:
        logger.info("Not overwriting config file")
        return
    
    config['webpage'] = {}
    config['webpage']['host_ip'] = webpage_host_ip
    config['webpage']['port'] = webpage_port
    config['webpage']['enabled'] = webserver_enabled

    config['zabbix'] = {}
    config['zabbix']['ip'] = zabbix_ip
    config['zabbix']['enabled'] = zabbix_enabled

    with open("./config.ini", "w") as config_file:
        config.write(config_file)

        
    logger.info("Config written to file")

def read_config():
    global webpage_host_ip, webpage_port, zabbix_enabled, webserver_enabled, zabbix_enabled, zabbix_ip
    config_exists = exists("./config.ini")
    if not config_exists:
        logger.warning("Config file not available to read from")
    
    config = configparser.ConfigParser()
    config.read('./config.ini')
    
    webpage_host_ip = config['webpage']['host_ip']
    webpage_port = int(config['webpage']['port'])
    webserver_enabled = config['webpage'].getboolean('enabled')

    zabbix_ip = config['zabbix']['ip']
    zabbix_enabled = config['zabbix'].getboolean('enabled')

    logger.info("Config loaded successfully")


config = configparser.ConfigParser()

log_file_handler = TimedRotatingFileHandler(filename='./runtime.log', when='D', interval=1, backupCount=10,
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

if webserver_enabled:
    webServer = HTTPServer((webpage_host_ip, webpage_port), JSONServer)
    logger.info("Server started http://%s:%s" % (webpage_host_ip, webpage_port))

    t = threading.Thread(target=start_web_server, args=(webServer,)).start()

logger.info("Entering main loop. Press Control-C to exit.")
try:
    timer = time.time()
    while True:
        
        msg = midiin.get_message()
        if msg:
            message, deltatime = msg
            timer += deltatime
            hex_message = list_to_hex(message)
            logger.debug(hex_message)
            interpret_hex(hex_message)
            if current_cue != None and cue_updated == True:
                logger.info(current_cue)

                packet = [
                    ZabbixMetric('GMA Main', 'cue', current_cue),
                ]

                if zabbix_enabled:
                    try:
                        result = ZabbixSender(zabbix_server=zabbix_ip, timeout = 1).send(packet)
                    except TimeoutError:
                        logger.error("Zabbix timed out")

        time.sleep(0.01)
except KeyboardInterrupt:
    print('')
finally:
    print("Exit.")
    midiin.close_port()
    
    del midiin
