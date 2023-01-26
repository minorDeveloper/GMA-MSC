# Copyright samlane.tech 2022-2023

# Dependencies (pip packages)
# py-zabbix > v1.1.7
# python-rtmidi > v1.4.9

# TODO:
# Logging
# Validate input
# Github
# Instructions at top
# Send logfiles to Zabbix

from __future__ import print_function

import logging
import sys
import time

from rtmidi.midiutil import open_midiinput

from pyzabbix import ZabbixMetric, ZabbixSender
from math import fsum

zabbix_enabled = True

current_cue = None
cue_updated = False

def list_to_hex(integer_list):
    hex_list = integer_list

    for idx, x in enumerate(integer_list):
        hex_list[idx] = hex(x).removeprefix('0x')

    return hex_list

def interpret_hex(hex_data):
    # Example input
    # ['f0', '7f', '0', '2', '1', '1', '30', '2e', '33', '35', '30', 'f7']
    # ['f0', '7f', '0', '2', '1', '4', '0', '0', '0', '0', '0', '30', '2e', '33', '31', '30', 'f7']

    if len(hex_data) < 12: return

    try:
        command_type = int(hex_data[5])
    except:
        print("FAILED")
        return


    match command_type:
        case 1:
            # GO
            interpret_go(hex_data[6:-1])
        case 4: 
            # Timed GO
            if len(hex_data) < 17: return
            interpret_go(hex_data[11:-1])


def remove_first_char(lst):
    char_lst = lst

    for idx, x in enumerate(lst):
        char_lst[idx] = list(x)[1:][0]

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

    
    # Remove the 3 from each string, 
    whole_part = list_to_num(list(map(int, remove_first_char(hex_cue[:decimal_index]))), False)
    decimal_part = list_to_num(list(map(int, remove_first_char(hex_cue[decimal_index+1:]))), True)
    combined = whole_part + decimal_part

    if combined == None: return
    if current_cue == combined: return
    
    current_cue = combined
    cue_updated = True



log = logging.getLogger('midiin_poll')
logging.basicConfig(level=logging.INFO)

# Prompts user for MIDI input port, unless a valid port number or name
# is given as the first argument on the command line.
# API backend defaults to ALSA on Linux.
port = 1 #sys.argv[1] if len(sys.argv) > 1 else None

try:
    midiin, port_name = open_midiinput(port)
except (EOFError, KeyboardInterrupt):
    sys.exit()

midiin.ignore_types(sysex=False, timing=False, active_sense=False)

print("Entering main loop. Press Control-C to exit.")
try:
    timer = time.time()
    while True:
        
        msg = midiin.get_message()
        if msg:
            message, deltatime = msg
            timer += deltatime
            interpret_hex(list_to_hex(message))
            if current_cue != None and cue_updated == True:
                print(current_cue)

                packet = [
                    ZabbixMetric('GMA Main', 'cue', current_cue),
                ]

                if zabbix_enabled:
                    try:
                        result = ZabbixSender(zabbix_server='192.168.0.116', timeout = 1).send(packet)
                    except TimeoutError:
                        logging.error("Zabbix timed out")

        time.sleep(0.01)
except KeyboardInterrupt:
    print('')
finally:
    print("Exit.")
    midiin.close_port()
    del midiin