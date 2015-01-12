# -*- coding: utf-8 -*-

"""
Python library for Paessler's PRTG (http://www.paessler.com/)
"""

import json
import xml.etree.ElementTree as Et
from urllib import request


class PrtgException(Exception):
    pass


class BadRequest(PrtgException):
    pass


class BadTarget(PrtgException):
    pass


class UnknownResponse(PrtgException):
    pass


class PrtgObject(object):
    """
    PRTG base object
    """

    column_table = {

        'all': [
            'objid', 'type', 'tags', 'active', 'name'
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
    }

    def __init__(self, **kwargs):
        for key in self.column_table['all']:
            try:
                self.__setattr__(key, kwargs[key])
            except KeyError:
                pass


class Sensor(PrtgObject):
    """
    PRTG sensor object
    """
    def __init__(self, **kwargs):
        PrtgObject.__init__(self, **kwargs)
        self.name = None
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
        self.name = None
        for key in self.column_table['devices']:
            try:
                self.__setattr__(key, kwargs[key])
            except KeyError:
                pass


class Query(object):

    targets = [
        'getobjectproperties', 'getobjectstatus', 'getsensordetails', 'getsensordetails', 'table', 'getstatus',
        'sensortypesinuse', 'getobjectproperty'
    ]

    args = []
    columns = []
    target = ''
    url_str = '{}/api/{}username={}&password={}&output={}'
    method = 'GET'

    def __init__(self, endpoint, target, username, password, output='json', **kwargs):

        if target not in self.targets:
            raise BadTarget('Invalid API target: {}'.format(target))

        self.endpoint = endpoint
        self.username = username
        self.password = password
        self.output = output
        self.method = 'GET'
        self.content = ''
        self.target = target + '.xml' + '?'
        self.paginate = False

        if 'counter' in kwargs:
            self.paginate = True
            self.counter = kwargs['counter']
            self._counter = 0
            self.finished = False

        if 'content' in kwargs:
            self.content = kwargs['content']

        self.extra = kwargs

    def increment(self, count, total):
        if self._counter + count >= total:
            self.finished = True
            self._counter = 0
            return
        self._counter += count

    def get_url(self):
        _url = self.url_str.format(self.endpoint, self.target, self.username, self.password, self.output)

        if self.paginate:
            _url += '&start={}'.format(self._counter)

        if self.extra:
            _url += '&' + '&'.join(map(lambda x: '{}={}'.format(x[0], x[1]),
                                       filter(lambda z: z[1], self.extra.items())))
        return _url

    def __str__(self):
        return self.get_url()


class Connection(object):

    def __init__(self, limit=500):
        self.limit = limit
        self._counter = 0
        self.finished = False

    def _process_response(self, response, query, paginate=False):

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
                return [Device(**x) for x in processed['sensors']], processed['treesize']

        if not processed:
            raise UnknownResponse('Unknown response: {}'.format(out))

    def _build_request(self, query):
        return request.Request(url=str(query), method=query.method)

    def paginate_request(self, query):
        while not query.finished:
            req = self._build_request(query)
            resp, size = self._process_response(request.urlopen(req), query, paginate=query.paginate)
            query.increment(len(resp), size)
            yield resp

    def make_request(self, query):
        req = self._build_request(query)
        resp = self._process_response(request.urlopen(req), query)
        return resp


class Client(object):

    def __init__(self, endpoint, username, password):
        self.connection = Connection()
        self.query_args = {'endpoint': endpoint, 'username': username, 'password': password}

    def _build_query(self, **kwargs):
        args = self.query_args.copy()
        args.update(kwargs)
        return Query(**args)

    def query(self, query):
        out = []
        if query.paginate:
            for r in self.connection.paginate_request(query):
                out.append(r)
            return out
        resp = self.connection.make_request(query)
        return resp

    def get_table_output(self, filter_string, content):
        k, v = filter_string.split('=')
        return self._build_query(
            target='table', content=content, counter=content, **{k: v}
        )

    def get_object_property(self, objectid, prop):
        return self._build_query(target='getobjectproperty', id=objectid, property=prop, show='text')

    def get_sensor(self, sensorid):
        return self._build_query(target='getsensordetails', sensorid=sensorid, output='xml', content='sensor')

    def get_status(self):
        return self._build_query(target='getstatus')

    def get_sensor_types(self):
        return self._build_query(target='sensortypesinuse')

    def set_object_property(self, objectid, name, value):
        return self._build_query(target='setobjectproperty', id=objectid, name=name, value=value)

