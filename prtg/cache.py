import shelve
import logging


class Cache(object):

    def __init__(self, cache_path='/tmp/prtg.cache'):
        self.cache_path = cache_path
        with shelve.open(self.cache_path) as cache:
            try:
                cache['sensors']
            except KeyError:
                cache['sensors'] = list()

            try:
                cache['devices']
            except KeyError:
                cache['devices'] = list()

    def write_content(self, content, bucket):
        with shelve.open(self.cache_path) as cache:
            # TODO: This needs to automatically detect its bucket.
            logging.info('Writing Cache')
            cache[bucket] = content

    def get_content(self, bucket):
        with shelve.open(self.cache_path) as cache:
            try:
                for c in cache[bucket]:
                    yield c
            except KeyError:
                yield None