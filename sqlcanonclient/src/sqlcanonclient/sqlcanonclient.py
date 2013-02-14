#!/usr/bin/env python

from datetime import datetime
import string
import urllib
import urllib2
import pcap
from construct.protocols.ipstack import ip_stack
import sys
import pprint
import argparse

PP = pprint.PrettyPrinter(indent=4)

PROCESS_CAPTURED_STATEMENT_URL = 'http://localhost:8000/canonicalizer/process_captured_statement/'

def process_packet(pktlen, data, timestamp):
    if not data:
        return

    print 'pktlen:', pktlen, 'dt:', datetime.fromtimestamp(timestamp)
    stack = ip_stack.parse(data)
    payload = stack.next.next.next
    print payload

    # MySQL queries start on the 6th char (?)
    payload = payload[5:]

    params = dict(statement=payload)
    params = urllib.urlencode(params)
    print params
    try:
        handler = urllib2.urlopen(PROCESS_CAPTURED_STATEMENT_URL, params)
        print 'handler.code:', handler.code
    except Exception, e:
        print 'Exception: {0}'.format(e)

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('interface', help='interface to sniff from')
    parser.add_argument('--filter', default='dst port 3306', help='pcap-filter')
    parser.add_argument(
        '--capture_url',
        help='URL of captured statement processor (default: http://localhost:8000/canonicalizer/process_captured_statement/)',
    )
    args = parser.parse_args()
    if args.capture_url:
        PROCESS_CAPTURED_STATEMENT_URL = args.capture_url
    print 'Sending captured statements to: {0}'.format(PROCESS_CAPTURED_STATEMENT_URL)

    #if len(sys.argv) < 3:
    #    print 'usage: {0} <interface> <expr>'.format(sys.argv[0])
    #    sys.exit()

    p = pcap.pcapObject()
    #dev = sys.argv[1]
    dev = args.interface
    net, mask = pcap.lookupnet(dev)
    print 'net:', net, 'mask:', mask

    # sample dev:
    #     eth0
    #     wlan0
    #     lo
    p.open_live(dev, 1600, 0, 100)

    # sample filter:
    #     dst port 3306
    # see: http://www.manpagez.com/man/7/pcap-filter/
    #p.setfilter(string.join(sys.argv[2:], ' '), 0, 0)
    p.setfilter(args.filter, 0, 0)

    print 'Press CTRL+C to end capture'
    try:
        while True:
            p.dispatch(1, process_packet)
    except KeyboardInterrupt:
        print # Empty line where ^C from CTRL+C is displayed
        print '%s' % sys.exc_type
        print 'shutting down'
        print '%d packets received, %d packets dropped, %d packets dropped by interface' % p.stats()
