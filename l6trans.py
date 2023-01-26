import sys
from datetime import datetime as dt
from config import config

'''
    translates incoming midi messages into
        human readable form

    #!/bin/sh : receivemidi dev "USB Uno MIDI Interface MIDI 1" | python l6trans.py

'''

tr_dict = { str(v): k for x in ['amp', 'mod'] for k, v in config['cc'][x].items() } 
tr_dict.update({
    '3': 'mod_tweak',
    '2': 'del_tweak',
    '89': 'tempo_msb',
    '90': 'tempo_lsb',
    '64': 'tempo_tap'
})

try:
    buff = ''
    while True:
        buff += sys.stdin.read(1)
        if buff.endswith('\n'):
            line = buff[:-1]
            tnow = dt.now()
            date = dt.strftime(tnow, '%b %d')
            time = dt.strftime(tnow, '%H:%M:%S')
            now  = date.lower() + ' ' + time
            try:
                items  = line.split()
                new    = tr_dict.get(items[3], items[3])
                val    = items[4]    
                print(f'{now}   {new:<13} {val}')
            except Exception as e:
                print(e)
                print(f'{now}   {line}')
            buff = ''
except KeyboardInterrupt:
    sys.stdout.flush()

