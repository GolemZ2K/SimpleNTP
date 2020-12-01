#!/usr/bin/env python3
#coding:utf-8
'''
Simple time synchronizer, to synchronization time in a lan.


usage: python3 sntp.py [-h] [-s] [-i interval]

SimpleNtp server and client

optional arguments:
  -h, --help   show this help message and exit
  -s           run as ntp server
  -i interval  interval of broadcasting (default: 5 seconds)
'''

import socket, traceback, json
import time, datetime, os, sys
import argparse
import ipaddress
import socket
import threading

ip  = socket.gethostbyname(socket.gethostname())
net = ipaddress.IPv4Network(ip + '/24', False)
ADDR = net.broadcast_address.compressed  # or just '192.168.1.255'
PORT = 6666
TIME_FORMAT = '%(year)s-%(month)s-%(day)s %(hour)s:%(minute)s:%(second)s.%(microsecond)s'

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
localtimezone = -time.timezone//3600
print('Local timezone:', localtimezone)
isLinux = 'linux' in sys.platform

def procCmdline():
    '''command line'''
    parser = argparse.ArgumentParser(description='SimpleNtp server and client', add_help=True)
    parser.add_argument('-s', action='store_true', default=False, help='run as ntp server')
    parser.add_argument('-i', type=int, default=5, metavar='interval', help='interval of broadcasting (default: 5 seconds)')
    args = parser.parse_args()
    args.i = args.i if args.i >= 1 else 5
    return args

def run(args):
    if args.s:
        server(args)
    else:
        client(args)

def toTimeDict(curtime):
    return {
        'year' : curtime.year,
        'month' : curtime.month,
        #'weekday' :curtime.weekday()+1,
        'day' : curtime.day,
        'hour' : curtime.hour,
        'minute' : curtime.minute,
        'second' : curtime.second,
        'microsecond' : curtime.microsecond
    }

def server(args):
    print ("MyNtp Server. ")
    print ("press Ctrl + c to stop ")

    dest = (ADDR, PORT)
    print ('Broadcasting time to %s every %d seconds'%(dest, args.i))

    while True:
        try:
            curtime = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
            timedict = toTimeDict(curtime)

            data = {'time' : timedict}
            msg = json.dumps(data)
            s.sendto(msg.encode('utf-8'), dest)

            curtime = curtime.astimezone(datetime.timezone(datetime.timedelta(hours=localtimezone)))
            timedict = toTimeDict(curtime)
            timestr = TIME_FORMAT % timedict
            print('Broadcasting time: %s'%timestr)

        except (KeyboardInterrupt, SystemExit):
            return
        except:
            traceback.print_exc()

        try:
            time.sleep(args.i)
        except (KeyboardInterrupt, SystemExit):
            print('')
            return

def client(args):
    print ("MyNtp Client. ")
    print ("press Ctrl + c to stop ")

    dest = ('', PORT)
    s.bind(dest)
    print ('Listening for broadcast at', s.getsockname())
    while True:
        try:
            message, addr = s.recvfrom(8192)
            data = json.loads(message.decode('utf-8'))
            timedict = data['time']

            curtime = datetime.datetime(**timedict).replace(tzinfo=datetime.timezone.utc)
            curtime = curtime.astimezone(datetime.timezone(datetime.timedelta(hours=localtimezone)))

            timedict = toTimeDict(curtime)
            timestr = TIME_FORMAT % timedict
            print('Got time: %s from %s'%(timestr, addr))

            if isLinux:
                os.system("date -s '%s';hwclock -w"%timestr)
            else:
                timedict['microsecond'] = str(timedict['microsecond'])[:2]  #for windows，only get first two number
                os.system('time %(hour)s:%(minute)s:%(second)s.%(microsecond)s'%timedict)
                os.system('date %(year)s-%(month)s-%(day)s'%timedict)

        except (KeyboardInterrupt, SystemExit):
            print('')
            return
        except:
            traceback.print_exc()

def main():
    args = procCmdline()
    t = threading.Thread(target=run, args=(args,))
    t.setDaemon(True)
    t.start()
    while True:
        try:
            time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            print('')
            return

if __name__ == '__main__':
    main()
