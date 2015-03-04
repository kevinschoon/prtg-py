# -*- coding: utf-8 -*-

"""
PrtgObject Models
"""

import re

from prtg.exceptions import BadTarget


class PrtgObject(object):
    """
    PRTG base object
    """

    column_table = {

        'all': [
            'objid', 'type', 'tags', 'active', 'name', 'status', 'parentid', 'result',
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


class Sensor(PrtgObject):
    """
    PRTG sensor object
    """

    content_type = 'sensors'

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

    content_type = 'devices'

    def __init__(self, **kwargs):
        PrtgObject.__init__(self, **kwargs)
        for key in self.column_table['devices']:
            try:
                self.__setattr__(key, kwargs[key])
            except KeyError:
                pass


class Status(PrtgObject):
    """
    PRTG Status Object
    """

    content_type = 'status'

    def __init__(self, **kwargs):
        PrtgObject.__init__(self, **kwargs)
        for key in self.column_table['status']:
            try:
                self.__setattr__(key, kwargs[key])
            except KeyError:
                pass


class Rule(object):
    pass


class NameMatch(Rule):
    def __init__(self, prtg_object, attribute, pattern, prop, value, update):
        self.object = prtg_object
        self.attribute = attribute
        self.pattern = pattern
        self.prop = prop
        self.value = value

    def evaluate(self):
        return re.match(self.pattern, self.object.__getattribute__(self.attribute))


class Query(object):
    """
    PRTG Query object. This objects will return the URL as a string and
    hold the response from the server.
    """

    targets = {
        'table': {'extension': '.xml?'}, 'getstatus': {'extension': '.xml?'}, 'getpasshash': {'extension': '.htm?'},
        'setobjectproperty': {'extension': '.htm?'}, 'getobjectproperty': {'extension': '.htm?'}
    }

    args = []
    target = ''

    url_str = '{}/api/{}username={}&password={}'
    method = 'GET'
    default_columns = ['objid', 'parentid', 'name', 'tags', 'active', 'status']

    def __init__(self, client, target, maximum=5, content='', objid=None, name=None, value=None):

        if target not in self.targets:
            raise BadTarget('Invalid API target: {}'.format(target))

        self.endpoint = client.endpoint
        self.username = client.username
        self.password = client.password
        self.method = 'GET'
        self.target = target + self.targets[target]['extension']
        self.paginate = False
        self.response = list()
        self.counter = 0
        self.maximum = maximum
        self.extra = dict()
        self.expect_response = True

        if target == 'table':
            self.extra.update({'columns': ','.join(self.default_columns)})

        if content:
            self.extra.update({'content': content})

        if target == 'setobjectproperty':
            if not all([objid, name, value]):
                raise BadTarget
            self.extra.update({'id': objid, 'name': name, 'value': value})
            self.expect_response = False  # PRTG doesn't respond with a message, just assume 200 is ok.

        if target == 'getobjectproperty':
            if not all([objid, name]):
                raise BadTarget
            self.extra.update({'id': objid, 'name': name})

    def increment(self):
        self.counter += self.maximum

    def get_url(self):
        _url = self.url_str.format(self.endpoint, self.target, self.username, self.password)

        _url += '&start={}&count={}'.format(self.counter, self.maximum)

        if self.extra:
            _url += '&' + '&'.join(map(lambda x: '{}={}'.format(x[0], x[1]),
                                       filter(lambda z: z[1], self.extra.items())))
        return _url

    def __str__(self):
        return self.get_url()