#!/usr/bin/python3
# -*- coding: utf-8 -*-

import time
import binascii
import struct
import serial
import sys
import os
import signal
from argparse import ArgumentParser
from pprint import pprint

import crc16


def ma_mi(data):
    ma, mi = struct.unpack('>BB', data)
    return '{:02d}.{:02d}'.format(ma, mi)


DEBUG=False
READ_BYTES = 1024
STX=0x02
ETX=0x03
ENQ=0x05
ACK=0x06
NAK=0x15
# Variables in the data-block of a Delta RPI M-series inverter,
# as far as I've been able to establish their meaning.
# The fields for each variable are as follows: 
# name, struct, size in bytes, decoder, multiplier-exponent (10^x), unit, SunSpec equivalent
DELTA_RPI = (
    ("SAP part number", "11s", str),
    ("SAP serial number", "13s", str),
    ("SAP date code", "4s", binascii.hexlify),
    ("SAP revision", "2s", binascii.hexlify),
    ("DSP FW Rev", "2s", ma_mi, 0, "MA,MI"),
    ("DSP FW Date", "2s", ma_mi, 0, "MA,MI"),
    ("Redundant MCU FW Rev", "2s", ma_mi, 0, "MA,MI"),
    ("Redundant MCU FW Date", "2s", ma_mi, 0, "MA,MI"),
    ("Display MCU FW Rev", "2s", ma_mi, 0, "MA,MI"),
    ("Display MCU FW Date", "2s", ma_mi, 0, "MA,MI"),
    ("Display WebPage Ctrl FW Rev", "2s", ma_mi, 0, "MA,MI"),
    ("Display WebPage Ctrl FW Date", "2s", ma_mi, 0, "MA,MI"),
    ("Display WiFi Ctrl FW Rev", "2s", ma_mi, 0, "MA,MI"),
    ("Display WiFi Ctrl FW Date", "2s", ma_mi, 0, "MA,MI"),
    ("AC Voltage(Phase1)", "H", float, -1, "V"),
    ("AC Current(Phase1)", "H", float, -2, "A", "AphA"),
    ("AC Power(Phase1)", "H", int, 0, "W"),
    ("AC Frequency(Phase1)", "H", float, -2, "Hz"),
    ("AC Voltage(Phase1) [Redundant]", "H", float, -1, "V"),
    ("AC Frequency(Phase1) [Redundant]", "H", float, -2, "Hz"),
    ("AC Voltage(Phase2)", "H", float, -1, "V"),
    ("AC Current(Phase2)", "H", float, -2, "A", "AphB"),
    ("AC Power(Phase2)", "H", int, 0, "W"),
    ("AC Frequency(Phase2)", "H", float, -2, "Hz"),
    ("AC Voltage(Phase2) [Redundant]", "H", float, -1, "V"),
    ("AC Frequency(Phase2) [Redundant]", "H", float, -2, "Hz"),
    ("AC Voltage(Phase3)", "H", float, -1, "V"),
    ("AC Current(Phase3)", "H", float, -2, "A", "AphC"),
    ("AC Power(Phase3)", "H", int, 0, "W"),
    ("AC Frequency(Phase3)", "H", float, -2, "Hz"),
    ("AC Voltage(Phase3) [Redundant]", "H", float, -1, "V"),
    ("AC Frequency(Phase3) [Redundant]", "H", float, -2, "Hz"),
    ("Solar Voltage at Input 1", "H", float, -1, "V"),
    ("Solar Current at Input 1", "H", float, -2, "A"),
    ("Solar Power at Input 1", "H", int, 0, "W"),
    ("Solar Voltage at Input 2", "H", float, -1, "V"),
    ("Solar Current at Input 2", "H", float, -2, "A"),
    ("Solar Power at Input 2", "H", int, 0, "W"),
    ("ACPower", "H", int, 0, "W"),
    ("(+) Bus Voltage", "H", float, -1, "V"),
    ("(-) Bus Voltage", "H", float, -1, "V"),
    ("Supplied ac energy today", "I", int, 0, "Wh"),
    ("Inverter runtime today", "I", int, 0, "second"),
    ("Supplied ac energy (total)", "I", int, 0, "Wh"),
    ("Inverter runtime (total)", "I", int, 0, "second"),
    ("Calculated temperature inside rack", "h", int, 0, "°C", "TmpSnk"),
    ("Status AC Output 1", "B", int),
    ("Status AC Output 2", "B", int),
    ("Status AC Output 3", "B", int),
    ("Status AC Output 4", "B", int),
    ("Status DC Input 1", "B", int),
    ("Status DC Input 2", "B", int),
    ("Error Status", "B", int),
    ("Error Status AC 1", "B", int),
    ("Global Error 1", "B", int),
    ("CPU Error", "B", int),
    ("Global Error 2", "B", int),
    ("Limits AC output 1", "B", int),
    ("Limits AC output 2", "B", int),
    ("Global Error 3", "B", int),
    ("Limits DC 1", "B", int),
    ("Limits DC 2", "B", int),
    ("History status messages", "20s", binascii.hexlify),
)
DELTA_RPI_STRUCT = '>' + ''.join([item[1] for item in DELTA_RPI])
DUMMY_DATA = (
    b'802FA0E1000',  # SAP part number
    b'O1S16300040WH',  # SAP serial number
    b'0901',  # SAP date code
    b'0\x00',  # SAP revision
    b'\x01#',  # DSP FW Rev
    b'\x0f0',  # DSP FW Date
    b'\x01\r',  # Redundant MCU FW Rev
    b'\x0f\x0e',  # Redundant MCU FW Date
    b'\x01\x10',  # Display MCU FW Rev
    b'\x0f0',  # Display MCU FW Date
    b'\x00\x00',  # Display WebPage Ctrl FW Rev
    b'\x00\x00',  # Display WebPage Ctrl FW Date
    b'\x00\x00',  # Display WiFi Ctrl FW Rev
    b'\x00\x00',  # Display WiFi Ctrl FW Date
    0,  # AC Voltage(Phase1)
    0,  # AC Current(Phase1)
    0,  # AC Power(Phase1)
    0,  # AC Frequency(Phase1)
    0,  # AC Voltage(Phase1) [Redundant]
    0,  # AC Frequency(Phase1) [Redundant]
    0,  # AC Voltage(Phase2)
    0,  # AC Current(Phase2)
    0,  # AC Power(Phase2)
    0,  # AC Frequency(Phase2)
    0,  # AC Voltage(Phase2) [Redundant]
    0,  # AC Frequency(Phase2) [Redundant]
    0,  # AC Voltage(Phase3)
    0,  # AC Current(Phase3)
    0,  # AC Power(Phase3)
    0,  # AC Frequency(Phase3)
    0,  # AC Voltage(Phase3) [Redundant]
    0,  # AC Frequency(Phase3) [Redundant]
    0,  # Solar Voltage at Input 1
    0,  # Solar Current at Input 1
    0,  # Solar Power at Input 1
    0,  # Solar Voltage at Input 2
    0,  # Solar Current at Input 2
    0,  # Solar Power at Input 2
    0,  # ACPower
    0,  # (+) Bus Voltage
    0,  # (-) Bus Voltage
    0,  # Supplied ac energy today
    0,  # Inverter runtime today
    0,  # Supplied ac energy (total)
    0,  # Inverter runtime (total)
    0,  # Calculated temperature inside rack
    0,  # Status AC Output 1
    0,  # Status AC Output 2
    0,  # Status AC Output 3
    0,  # Status AC Output 4
    0,  # Status DC Input 1
    0,  # Status DC Input 2
    0,  # Error Status
    0,  # Error Status AC 1
    0,  # Global Error 1
    0,  # CPU Error
    0,  # Global Error 2
    0,  # Limits AC output 1
    0,  # Limits AC output 2
    0,  # Global Error 3
    0,  # Limits DC 1
    0,  # Limits DC 2
    b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',  # History status messages
)


def signal_handler(signal, frame):
    ''' Catch SIGINT/SIGTERM/SIGKILL and exit gracefully '''
    print("Stop requested...")
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def send(conn, req, cmd, subcmd, data=b'', addr=1):
    """
    Send cmd/subcmd (e.g. 0x60/0x01) and optional data to the RS485 bus
    """
    assert req in (ENQ, ACK, NAK)  # req should be one of ENQ, ACK, NAK
    msg = struct.pack('BBBBB', req, addr, 2 + len(data), cmd, subcmd)
    if len(data) > 0:
        msg = struct.pack('5s%ds' % len(data), msg, data)
    crcval = crc16.calcData(msg)
    lsb = crcval & (0xff)
    msb = (crcval >> 8) & 0xff
    data = struct.pack('B%dsBBB' % len(msg), STX, msg, lsb, msb, ETX)
    if DEBUG: print(">>> SEND:", binascii.hexlify(msg), "=>", binascii.hexlify(data))
    conn.write(data)
    conn.flush()


def receive(conn):
    """ 
    Attempt to read messages from a serial connection
    """
    data = bytearray()
    while True:
        buf = conn.read(READ_BYTES)
        if buf:
            if DEBUG: print(">>> RAW RECEIVE:", buf)
            data.extend(buf)
        if (not buf) or len(buf) < READ_BYTES:
            break

    idx = 0
    while idx + 9 <= len(data):
        if data[idx] != STX:
            idx += 1
            continue
        stx, req, addr, size = struct.unpack('>BBBB', data[idx:idx+4])
        if req not in (ENQ, ACK, NAK):
            print("Bad req value: {:02x} (should be one of ENQ/ACK/NAK)".format(req))
            idx += 1
            continue
        if idx + 4 + size >= len(data):
            print("Can't read %d bytes from buffer" % size)
            idx += 1
            continue
        msg, lsb, msb, etx = struct.unpack('>%dsBBB' % size, data[idx+4:idx+7+size])
        if etx != ETX:
            print("Bad ETX value: {:02x}".format(etx))
            idx += 1
            continue
        crc_calc = crc16.calcData(data[idx+1:idx+4+size])
        crc_msg = msb << 8 | lsb
        if crc_calc != crc_msg:
            print("Bad CRC check: %s <> %s" % (binascii.hexlify(crc_calc), binascii.hexlify(crc_msg)))
            idx += 1
            continue

        if DEBUG: print(">>> RECV:", binascii.hexlify(data), "=>", binascii.hexlify(msg))
        yield {
            "stx": stx,
            "req": req,
            "addr": addr,
            "size": size,
            "msg": msg,
            "lsb": lsb,
            "msb": msb,
            "etx": etx,
        }
        idx += 4 + size
            

def decode_msg(data):
    req = data['req']
    cmd, cmdsub = struct.unpack('>BB', data['msg'][0:2])
    data['cmd'] = cmd
    data['cmdsub'] = cmdsub
    data['raw'] = data['msg'][2:]
    if req == NAK:
        print("NAK value received: cmd/subcmd request was invalid".format(req))
    elif req == ENQ:
        if DEBUG: print("ENQ value received: request from master (datalogger)")
    elif req == ACK:
        if DEBUG: print("ACK value received: response from slave (inverter)")
        data['values'] = struct.unpack(DELTA_RPI_STRUCT, data['raw'])
    if DEBUG: pprint(data)
    return data


def main():
    global DEBUG, MODE
    parser = ArgumentParser(description='Delta inverter simulator (slave mode) or datalogger (master mode) for RPI M8A')
    parser.add_argument('-a', metavar='ADDRESS', type=int,
                      default=1,
                      help='slave address [default: 1]')
    parser.add_argument('-d', metavar='DEVICE',
                      default='/dev/ttyUSB0',
                      help='serial device port [default: /dev/ttyUSB0]')
    parser.add_argument('-b', metavar='BAUDRATE',
                      default=9600,
                      help='baud rate [default: 9600]')
    parser.add_argument('-t', metavar='TIMEOUT', type=float,
                      default=2.0,
                      help='timeout, in seconds (can be fractional, such as 1.5) [default: 2.0]')
    parser.add_argument('--debug', action="store_true",
                      help='show debug information')
    parser.add_argument('mode', metavar='MODE', choices=['master', 'slave'],
                      help='mode can either be "master" or "slave"')

    args = parser.parse_args()
    DEBUG = args.debug
    MODE = args.mode

    conn = serial.Serial(args.d, args.b, timeout=args.t);
    conn.flushOutput()
    conn.flushInput()
    while True:
        if MODE == 'master':
            send(conn, ENQ, 0x60, 0x01, addr=args.a)
            time.sleep(0.1)
        for data in receive(conn):
            if MODE == 'master' and data['addr'] == args.a and data['req'] in (ACK, NAK,):
                d = decode_msg(data)
                if d['req'] == ACK:
                    if not (d['cmd'] == 0x60 and d['cmdsub'] == 0x01):
                        print("Can't decode request cmd=0x%02X, cmdsub=0x%02X" % (d['cmd'], d['cmdsub']))
                        print("The only supported request is cmd=0x60, cmdsub=0x01")
                        continue
                    print(61 * '=')
                    for i, item in enumerate(DELTA_RPI):
                        label = item[0]
                        decoder = item[2]
                        scale = item[3] if len(item) > 3 else 0
                        units = item[4] if len(item) > 4 else ''
                        value = decoder(data['values'][i])
                        if decoder == float:
                            value = value * pow(10, scale)
                        print('%-40s %20s %-10s' % (label, value, units))
            if MODE == 'slave' and data['addr'] == args.a and data['req'] in (ENQ,):
                d = decode_msg(data)
                if d['cmd'] == 0x60 and d['cmdsub'] == 0x01:
                    raw = struct.pack(DELTA_RPI_STRUCT, *DUMMY_DATA)
                    send(conn, ACK, 0x60, 0x01, data=raw, addr=args.a)
                else:
                    print("This simulator only replies to cmd=0x60 cmdsub=0x01 requests...")


if __name__ == "__main__":
    main()
