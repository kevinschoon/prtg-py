# -*- coding: utf-8 -*-
"""
Unittests for PRTG Query Builder
"""

import unittest
import re
from prtg import Client


class TestQueryBuilder(unittest.TestCase):

    def setUp(self):
        self.endpoint = 'https://prtg.randomcompany.com'
        self.username = 'UserName'
        self.password = 'SecretPw'
        self.client = PrtgClient(self.endpoint, self.username, self.password)

    def test_get_object(self):
        target = 'getobjectproperty.xml'
        query = self.client.get_object(objectid=1234)
        r = re.compile(r'((https://prtg\.randomcompany.com)/api/(.*)\?username=(.*)&password=(.*)&objectid=(.*))')
        m = r.match(str(query))
        assert m.group(2) == self.endpoint
        assert m.group(3) == target
        assert m.group(4) == self.username
        assert m.group(5) == self.password
        assert m.group(6) == '1234'


class TestQueryCounter(unittest.TestCase):

    def setUp(self):
        pass

    def test_get_objects(self):
        pass
