#!/usr/bin/python

import time
import struct
import os
import sys
import serial
import binascii

sequence_number = 5

def get_sequence_number():
    global sequence_number

    return sequence_number

def next_sequence_number():
    global sequence_number

    sequence_number = (sequence_number + 1 ) % (1 << 24)

def FlushInput(ser):
    while ser.inWaiting():
        ch = ser.read(1)
        if len(ch) != 1:
            return

def do_sync(device):
    print("+++ Connecting to the BUSSide")
    try:
        ser = serial.Serial(device, 500000, timeout=2)
        print("+++ Initiating comms");
        FlushInput(ser)
        ser.close() # some weird bug
    except Exception, e:
        print(e)
        ser.close()
        print("*** BUSSide connection error")
        return -1
    try:
        ser = serial.Serial(device, 500000, timeout=2)
        FlushInput(ser)
    except Exception, e:
        print(e)
        ser.close()
        print("*** BUSSide connection error")
        return -1
    print("+++ Sending echo command")
    try:
        bs_command = struct.pack('<I', 0)
        bs_command_length = struct.pack('<I', 0)
        bs_request_args = struct.pack('<I', 0) * 256
        request  = bs_command
        request += bs_command_length
        saved_sequence_number = get_sequence_number()
        next_sequence_number()
        request += struct.pack('<I', saved_sequence_number)
        request += bs_request_args
        crc = binascii.crc32(request)
        request += struct.pack('<i', crc)
        ser.write(request)
        bs_command = ser.read(4)
        bs_reply_length = ser.read(4)
        bs_sequence_number = ser.read(4)
        reply  = bs_command
        reply += bs_reply_length
        reply += bs_sequence_number
        bs_reply_args = list(range(256))
        for i in range(256):
            s = ser.read(4)
            reply += s
            bs_reply_args[i], = struct.unpack('<I', s)
        bs_checksum, = struct.unpack('<i', ser.read(4))
        crc = binascii.crc32(reply)
        if crc != bs_checksum:
            return -1
        seq, = struct.unpack('<I', bs_sequence_number)
        if saved_sequence_number != seq:
            return -2
        ser.close()
        return 0
    except Exception, e:
        print(e)
        ser.close()
        return -1

def sync(device):
    for j in range(10):
        try:
            rv = -2
            while rv == -2:
                rv = do_sync(device)
                if rv == 0:
                    return 0
        except Exception, e:
            print(e)
        print("--- Warning. Retransmiting Attempt #%d" % (j+1))
        time.sleep(2)
    return -1
