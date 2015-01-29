# -*- coding: utf-8 -*-
"""
Python library for Paessler's PRTG (http://www.paessler.com/)
"""

import json
import xml.etree.ElementTree as Et
from urllib import request
import logging


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


class Query(object):
    """
    PRTG Query object. This objects will return the URL as a string and
    hold the response from the server.
    """

    targets = {
        'table': {'extension': '.xml?'}, 'getstatus': {'extension': '.xml?'}, 'getpasshash': {'extension': '.htm?'}
    }

    args = []
    columns = []
    target = ''
    url_str = '{}/api/{}username={}&password={}&output={}'
    method = 'GET'

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

    def paginate_request(self, query):
        """
        Paginate a large request into several HTTP requests.
        """
        while not query.finished:
            req = self._build_request(query)
            resp, tree_size = self._process_response(request.urlopen(req), query, paginate=query.paginate)
            query.response += resp
            query.increment(tree_size)
            logging.info('Processed {} of {} objects'.format(query.start, tree_size))

    def make_request(self, query):
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

    def __init__(self, endpoint, username, password):
        self.connection = Connection()
        self.query_args = {'endpoint': endpoint, 'username': username, 'password': password}

    def _build_query(self, **kwargs):
        """
        Generate a Query object
        :param kwargs: dict
        :return: Query
        """
        args = self.query_args.copy()
        args.update(kwargs)
        q = Query(**args)
        logging.debug('Build query: {}'.format(q))
        return q

    def query(self, query):
        """
        Make a query against the PRTG API
        :param query: Query
        :return: Query
        """
        if query.paginate:
            self.connection.paginate_request(query)
            return query
        self.connection.make_request(query)
        return query

    def table(self, content, objid=None, filter_string=None,
                         columns=','.join(PrtgObject.column_table['all'])):
        """
        Get table output from the PRTG server
        :param content: str
        :param objid: str
        :param filter_string: str
        :param columns: list
        :return: Query
        """

        options = dict()

        if filter_string:
            k, v = filter_string.split('=')
            options.update({k: v})

        if objid:
            options.update({'id': objid})

        options.update({'columns': columns})

        return self._build_query(target='table', content=content, counter=content, **options)

    def status(self):
        """
        Get the status of the PRTG server
        :return: Query
        """
        return self._build_query(target='getstatus', output='xml')

    def set_object_property(self, objectid, name, value):
        """
        Set the property of an object
        :param objectid:
        :param name:
        :param value:
        :return:
        """
        return self._build_query(target='setobjectproperty', id=objectid, name=name, value=value)