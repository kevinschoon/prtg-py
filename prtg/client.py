# -*- coding: utf-8 -*-
"""
Python library for Paessler's PRTG (http://www.paessler.com/)
"""

import json
import logging
import xml.etree.ElementTree as Et
import re

from urllib import request
from prtg.cache import Cache


class PrtgException(Exception):
    """
    Base PRTG Exception
    """
    pass


class BadRequest(PrtgException):
    """
    Bad request
    """
    pass


class BadTarget(PrtgException):
    """
    Invalid target
    """
    pass


class UnknownResponse(PrtgException):
    """
    Unknown response
    """
    pass


class PrtgObject(object):
    """
    PRTG base object
    """

    column_table = {

        'all': [
            'objid', 'type', 'tags', 'active', 'name', 'status', 'parentid',
        ],
        'sensors': [
            'downtime', 'downtimetime', 'downtimesince', 'uptime', 'uptimetime', 'uptimesince', 'knowntime',
            'cumsince', 'sensor', 'interval', 'lastcheck', 'lastup', 'lastdown', 'device', 'group', 'probe',
            'grpdev', 'notifiesx', 'intervalx', 'access', 'dependency', 'probegroupdevice', 'status', 'message',
            'priority', 'lastvalue', 'upsens', 'downsens', 'downacksens', 'partialdownsens', 'warnsens',
            'pausedsens', 'unusualsens', 'undefinedsens', 'totalsens', 'favorite', 'schedule', 'minigraph', 'comments',
            'parentid'
        ],
        'devices': [
            'device', 'group', 'probe', 'grpdev', 'notifiesx', 'intervalx', 'access', 'dependency',
            'probegroupdevice', 'status', 'message', 'priority', 'upsens', 'downsens', 'downacksens',
            'partialdownsens', 'warnsens', 'pausedsens', 'unusualsens', 'undefinedsens', 'totalsens',
            'favorite', 'schedule', 'deviceicon', 'host', 'comments', 'icon', 'location', 'parentid'
        ],
        'status': [
            'NewMessages', 'NewAlarms', 'Alarms', 'AckAlarms', 'NewToDos', 'Clock', 'ActivationStatusMessage',
            'BackgroundTasks', 'CorrelationTasks', 'AutoDiscoTasks', 'Version', 'PRTGUpdateAvailable', 'IsAdminUser',
            'IsCluster', 'ReadOnlyUser', 'ReadOnlyAllowAcknowledge'
        ]
    }

    def __init__(self, **kwargs):
        self.type = str(self.__class__.__name__)
        for key in self.column_table['all']:
            try:
                value = kwargs[key]
                if key == 'tags':  # Process tags as a list
                    if isinstance(value, str):
                        value = value.split(' ')
                if key == 'objid':
                    value = int(value)
                if key == 'parentid':
                    value = int(value)
                self.__setattr__(key, value)
            except KeyError:
                pass

    def to_json(self):
        return json.dumps(self.__dict__)

    def __str__(self):
        return self.to_json()


class Sensor(PrtgObject):
    """
    PRTG sensor object
    """
    def __init__(self, **kwargs):
        PrtgObject.__init__(self, **kwargs)
        for key in self.column_table['sensors']:
            try:
                self.__setattr__(key, kwargs[key])
            except KeyError:
                pass


class Device(PrtgObject):
    """
    PRTG device object
    """
    def __init__(self, **kwargs):
        PrtgObject.__init__(self, **kwargs)
        for key in self.column_table['devices']:
            try:
                self.__setattr__(key, kwargs[key])
            except KeyError:
                pass

    def sensors_query(self):
        pass


class Status(PrtgObject):
    """
    PRTG Status Object
    """
    def __init__(self, **kwargs):
        PrtgObject.__init__(self, **kwargs)
        for key in self.column_table['status']:
            try:
                self.__setattr__(key, kwargs[key])
            except KeyError:
                pass


class Condition(object):
    def __init__(self, prtg_object, expression=None, attribute=None, tag=None):
        self.object = prtg_object
        self.expression = expression
        self.attribute = attribute
        self.tag = tag

    def __bool__(self):
        return isinstance(self.object, PrtgObject)


class RegexMatch(Condition):
    def __bool__(self):
        match = re.match(self.expression, self.object.__getattribute__(self.attribute))
        if match:
            return True
        return False


class HasTag(Condition):
    def __bool__(self):
        return self.tag in self.object.tags


class Query(object):
    """
    PRTG Query object. This objects will return the URL as a string and
    hold the response from the server.
    """

    targets = {
        'table': {'extension': '.xml?'}, 'getstatus': {'extension': '.xml?'}, 'getpasshash': {'extension': '.htm?'}
    }

    args = []
    target = ''

    url_str = '{}/api/{}username={}&password={}&output={}'
    method = 'GET'
    default_columns = ['objid', 'parentid', 'name', 'tags', 'active']

    def __init__(self, endpoint, target, username, password, output='json', max=500, **kwargs):
        logging.info('Loading client: {} {}'.format(endpoint, target))

        if target not in self.targets:
            raise BadTarget('Invalid API target: {}'.format(target))

        self.endpoint = endpoint
        self.username = username
        self.password = password
        self.output = output
        self.method = 'GET'
        self.content = ''
        self.target = target + self.targets[target]['extension']
        self.paginate = False
        self.response = list()
        self.start = 0
        self.count = max
        self.max = max
        self.finished = False

        if target == 'table':
            kwargs.update({'columns': ','.join(self.default_columns)})

        if 'counter' in kwargs:
            self.paginate = True
            self.counter = kwargs['counter']

        if 'content' in kwargs:
            self.content = kwargs['content']

        self.extra = kwargs

    def increment(self, tree_size):
        self.start = len(self.response)
        if self.start + self.max >= tree_size:
            self.count = tree_size - self.start
        if len(self.response) >= tree_size:
            self.finished = True

    def get_url(self):
        _url = self.url_str.format(self.endpoint, self.target, self.username, self.password, self.output)

        if self.paginate:
            _url += '&start={}&count={}'.format(self.start, self.count)

        if self.extra:
            _url += '&' + '&'.join(map(lambda x: '{}={}'.format(x[0], x[1]),
                                       filter(lambda z: z[1], self.extra.items())))

        logging.info('Got URL: {}'.format(_url))
        return _url

    def __str__(self):
        return self.get_url()


class Connection(object):
    """
    PRTG Connection Object
    """

    @staticmethod
    def _process_response(response, query, paginate=False):
        """
        Process the response from the server.
        """

        processed = None
        out = None

        if query.output == 'json':
            out = response.read().decode('utf-8')
            processed = json.loads(out)

        if query.output == 'xml':
            out = response.read().decode('utf-8')
            processed = Et.fromstring(out)

        if paginate:

            if all([query.content == 'sensors', processed]):
                return [Sensor(**x) for x in processed['sensors']], processed['treesize']

            if all([query.content == 'devices', processed]):
                return [Device(**x) for x in processed['devices']], processed['treesize']

        if query.target == 'getstatus.xml?':
            st = dict()
            for status in processed.iter('status'):
                for attrib in status:
                    st[attrib.tag] = attrib.text
            return Status(**st)

        if not processed:
            raise UnknownResponse('Unknown response: {}'.format(out))

        return processed

    def _build_request(self, query):
        """
        Build the HTTP request.
        """
        req, method = str(query), query.method
        logging.debug('REQUEST: target={} method={}'.format(req, method))
        return request.Request(url=req, method=method)

    def get_paginated_request(self, query):
        """
        Paginate a large request into several HTTP requests.
        """
        while not query.finished:
            req = self._build_request(query)
            resp, tree_size = self._process_response(request.urlopen(req), query, paginate=query.paginate)
            query.response += resp
            query.increment(tree_size)
            logging.info('Processed {} of {} objects'.format(query.start, tree_size))

    def get_request(self, query):
        """
        Make a single HTTP request
        """
        req = self._build_request(query)
        query.response.append(self._process_response(request.urlopen(req), query))
        return query


class Client(object):
    """
    Main PRTG client object. The client accepts PRTG Queries, handles the request, and updates the "response" attribute.
    """

    cache_path = '/tmp/prtg_json_cache.json'

    def __init__(self, endpoint, username, password, use_cache=False):
        self.connection = Connection()
        self.endpoint = endpoint
        self.username = username
        self.password = password

        self.use_cache = use_cache
        self.cache = Cache()

    def query(self, query):
        """
        Make a query against the PRTG API
        :param query: Query
        :return: Query
        """

        cache = self.cache.get_content(query)

        if cache:
            logging.warning('Loading cached response')
            query.response = cache

        else:

            if query.paginate:
                self.connection.get_paginated_request(query)
            else:
                self.connection.get_request(query)

            self.cache.write_content(query.response, query.content)

        return query

    def refresh(self, content='devices'):
        logging.info('Refreshing content: {}'.format(content))
        devices = Query(target='table', endpoint=self.endpoint, username=self.username, password=self.password, content=content, counter=content)
        self.connection.get_paginated_request(devices)
        self.cache.write_content(devices, content)

    def update(self, content, attribute, value, method='update'):
        for obj in content:
            logging.info('Updating object: {} with {}={}'.format(obj, attribute, value))
            if attribute == 'tags':
                if method == 'update':
                    obj.tags += value.split(',')
                elif method == 'replace':
                    obj.tags = value.split(',')
        self.cache.write_content(content, 'devices')

    def content(self, content, parents=False, regex=None, attribute=None):

        response = list()

        for resp in self.cache.get_content(content):

            if all([not regex, not attribute]):
                response.append(resp)

            elif all([regex, attribute]):
                if RegexMatch(resp, expression=regex, attribute=attribute):
                    response.append(resp)

        if all([content == 'sensors', parents is True]):
            p = list()
            for child in response:
                p += [x for x in self.cache.get_content('devices') if child.parentid == x.objid]

            response = p

        return response

    def status(self):
        status = Query(
            endpoint=self.endpoint, username=self.username, password=self.password,
            target='getstatus', output='xml'
        )
        self.connection.get_request(status)
        return status.response