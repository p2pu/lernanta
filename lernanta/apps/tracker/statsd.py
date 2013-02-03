# python_example.py

# Steve Ivy <steveivy@gmail.com>
# http://monkinetic.com
 
# this file expects local_settings.py to be in the same dir, with statsd host and port information:
# 
# statsd_host = 'localhost'
# statsd_port = 8125

import random
import sys
from pprint import pprint
from socket import socket, AF_INET, SOCK_DGRAM
import logging

from django.conf import settings
from django.contrib.sites.models import Site

log = logging.getLogger(__name__)


# Sends statistics to the stats daemon over UDP
class Statsd(object):
    
    @staticmethod
    def timing(stat, time, sample_rate=1):
        """
        Log timing information
        >>> from tracker.statsd import Statsd
        >>> Statsd.timing('some.time', 500)
        """
        stats = {}
        stats[stat] = "%d|ms" % time
        Statsd.send(stats, sample_rate)

    @staticmethod
    def increment(stats, sample_rate=1):
        """
        Increments one or more stats counters
        >>> Statsd.increment('some.int')
        >>> Statsd.increment('some.int',0.5)
        """
        Statsd.update_stats(stats, 1, sample_rate)

    @staticmethod
    def decrement(stats, sample_rate=1):
        """
        Decrements one or more stats counters
        >>> Statsd.decrement('some.int')
        """
        Statsd.update_stats(stats, -1, sample_rate)
    
    @staticmethod
    def update_stats(stats, delta=1, sampleRate=1):
        """
        Updates one or more stats counters by arbitrary amounts
        >>> Statsd.update_stats('some.int',10)
        """
        if (type(stats) is not list):
            stats = [stats]
        data = {}
        for stat in stats:
            data[stat] = "%s|c" % delta

        Statsd.send(data, sampleRate)
    
    @staticmethod
    def send(data, sample_rate=1):
        """
        Squirt the metrics over UDP
        """
        #TODO - disabling statsd for now
        return
        try:
            host = settings.STATSD_HOST
            port = settings.STATSD_PORT
            addr=(host, port)
        except AttributeError:
            log.debug('statsd not configured properly')
            return
        
        sampled_data = {}
        
        if(sample_rate < 1):
            if random.random() <= sample_rate:
                for stat in data.keys():
                    value = data[stat]
                    sampled_data[stat] = "%s|@%s" %(value, sample_rate)
        else:
            sampled_data=data

        domain = Site.objects.get_current().domain

        udp_sock = socket(AF_INET, SOCK_DGRAM)
        try:
            for stat in sampled_data.keys():
                value = data[stat]
                send_data = "%s.%s:%s" % (domain, stat, value)
                udp_sock.sendto(send_data, addr)
        except:
            log.error("Unexpected error at statsd: %s" % pprint(sys.exc_info()))

