# -*- coding: utf-8 -*-
"""
Unittests for PRTG Query Builder
"""

import unittest
from prtg.models import Query
from prtg.client import Client, Connection, Sensor, Device, Status, PrtgObject

username = 'prtgadmin'
password = 'prtgadmin'
endpoint = 'http://192.168.59.103'


class TestQuery(unittest.TestCase):

    def test_simple_query(self):
        client = Client(endpoint=endpoint, username=username, password=password)
        query = Query(client=client, target='table')
        self.assertIsInstance(query, Query)
        self.assertIn(endpoint, str(query))
        self.assertIn(username, str(query))
        self.assertIn(password, str(query))

    def test_status_query(self):
        client = Client(endpoint=endpoint, username=username, password=password)
        query = Query(client=client, target='getstatus')
        self.assertIsInstance(query, Query)

    def test_set_object_property_query(self):
        client = Client(endpoint=endpoint, username=username, password=password)
        query = Query(client=client, target='setobjectproperty', objid='2001', name='tags', value='"some new tags"')
        self.assertIsInstance(query, Query)

    def test_get_object_property_query(self):
        client = Client(endpoint=endpoint, username=username, password=password)
        query = Query(client=client, target='getobjectproperty', objid='2001', name='tags')
        self.assertIsInstance(query, Query)


class TestClient(unittest.TestCase):

    def test_get_object_property(self):
        client = Client(endpoint=endpoint, username=username, password=password)
        query = Query(client=client, target='getobjectproperty', objid='2001', name='tags')
        r = client.query(query)
        for obj in r:
            self.assertIsInstance(obj, PrtgObject)

    def test_set_object_property(self):
        client = Client(endpoint=endpoint, username=username, password=password)
        query = Query(client=client, target='setobjectproperty', objid='2001', name='tags', value='some new tags')
        client.query(query)

    def test_devices(self):
        client = Client(endpoint=endpoint, username=username, password=password)
        query = Query(client=client, target='table', content='devices')
        r = client.query(query)
        for device in r:
            self.assertIsInstance(device, Device)

    def test_sensors(self):
        client = Client(endpoint=endpoint, username=username, password=password)
        query = Query(client=client, target='table', content='sensors')
        r = client.query(query)
        for sensor in r:
            self.assertIsInstance(sensor, Sensor)

    def test_status(self):
        client = Client(endpoint=endpoint, username=username, password=password)
        query = Query(client=client, target='getstatus')
        r = client.query(query)
        for status in r:
            self.assertIsInstance(status, Status)


class TestConnection(unittest.TestCase):

    def test_simple_connection(self):
        c = Connection()
        self.assertIsInstance(c, Connection)


class TestSensor(unittest.TestCase):

    def test_sensor(self):
        s = Sensor()
        self.assertIsInstance(s, Sensor)


class TestDevice(unittest.TestCase):

    def test_device(self):
        d = Device()
        self.assertIsInstance(d, Device)


class TestStatus(unittest.TestCase):

    def test_status(self):
        s = Status()
        self.assertIsInstance(s, Status)


if __name__ == '__main__':
    unittest.main()
