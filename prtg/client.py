# -*- coding: utf-8 -*-
"""
Python library for Paessler's PRTG (http://www.paessler.com/)
"""

import logging
import xml.etree.ElementTree as Et

from urllib import request
from prtg.cache import Cache
from prtg.models import Sensor, Device, Status, PrtgObject
from prtg.exceptions import BadTarget, UnknownResponse


class Connection(object):
    """
    PRTG Connection Object
    """

    def __init__(self):
        self.response = list()

    @staticmethod
    def _encode_response(response, tag):
        out = list()
        if any([tag == 'devices', tag =='sensors']):
            for item in response.findall('item'):
                i = dict()
                for attrib in item:
                    i[attrib.tag] = attrib.text
                if tag == 'devices':
                    out.append(Device(**i))
                if tag == 'sensors':
                    out.append(Sensor(**i))

        if tag == 'status':
            i = dict()
            for item in response:
                i[item.tag] = item.text
            out.append(Status(**i))

        if tag == 'prtg':
            i = dict()
            for item in response:
                i[item.tag] = item.text
            out.append(PrtgObject(**i))

        return out

    def _process_response(self, response, expect_return=True):
        """
        Process the response from the server.
        """

        if expect_return:

            try:
                resp = Et.fromstring(response.read().decode('utf-8'))
            except Et.ParseError as e:
                raise UnknownResponse(e)
            try:
                ended = resp.attrib['listend']  # Catch KeyError and return finished
            except KeyError:
                ended = 1

            return self._encode_response(resp, resp.tag), ended

    def _build_request(self, query):
        """
        Build the HTTP request.
        """
        req, method = str(query), query.method
        logging.debug('REQUEST: target={} method={}'.format(req, method))
        return request.Request(url=req, method=method)

    def get_request(self, query):
        """
        Make a single HTTP request
        """
        req = self._build_request(query)
        logging.info('Making request: {}'.format(query))
        resp, ended = self._process_response(request.urlopen(req))
        self.response += resp
        if not int(ended):  # Recursively request until PRTG indicates "listend"
            query.increment()
            self.get_request(query)


class Client(object):

    def __init__(self, endpoint, username, password):
        self.endpoint = endpoint
        self.username = username
        self.password = password
        self.cache = Cache()

    @staticmethod
    def query(query):
        conn = Connection()
        conn.get_request(query)
        return conn.response

"""
    def refresh(self, query):
        logging.info('Refreshing content: {}'.format(content))
        devices = Query(target='table', endpoint=self.endpoint, username=self.username, password=self.password, content=content, counter=content)
        self.connection.get_paginated_request(devices)
        self.cache.write_content(devices.response)

    def update(self, content, attribute, value, replace=False):
        for index, obj in enumerate(content):
            logging.debug('Updating object: {} with {}={}'.format(obj, attribute, value))
            if attribute == 'tags':
                tags = value.split(',')
                if replace:
                    obj.tags = value.split(',')
                else:
                    obj.tags += [x for x in tags if x not in obj.tags]
            content[index] = obj
        self.cache.write_content(content, force=True)

    def content(self, content_name, parents=False, regex=None, attribute=None):
        response = list()
        for resp in self.cache.get_content(content_name):
            if not all([regex, attribute]):
                response.append(resp)
            else:
                if RegexMatch(resp, expression=regex, attribute=attribute):
                    response.append(resp)
        if all([content_name == 'sensors', parents is True]):
            logging.info('Searching for parents.. this may take a while')
            p = list()
            ids = set()
            for index, child in enumerate(response):
                parent = self.cache.get_object(str(child.parentid))  # Parent device.
                if parent:
                    ids.add(str(parent.objid))  # Lookup unique parent ids.
                else:
                    logging.warning('Unable to find sensor parent')
            for parent in ids:
                p.append(self.cache.get_object(parent))
            response = p
        return response
"""

