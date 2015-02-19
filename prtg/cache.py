import shelve
import logging


class Cache(object):

    def __init__(self, cache_path='/tmp/prtg.cache'):
        self.cache_path = cache_path
        with shelve.open(self.cache_path) as cache:
            try:
                cache['sensors']
            except KeyError:
                cache['sensors'] = dict()

            try:
                cache['devices']
            except KeyError:
                cache['devices'] = dict()

            try:
                cache['status']
            except KeyError:
                cache['status'] = dict()

    def write_content(self, content, force=False):
        with shelve.open(self.cache_path) as cache:
            logging.info('Writing Cache')
            for obj in content:
                if any([not str(obj.objid) in cache, force]):
                    # TODO: Compare new objects with cached objects.
                    logging.debug('Writing object {} to cache'.format(str(obj.objid)))
                    cache[str(obj.objid)] = obj
                else:
                    logging.debug('Object {} already cached'.format(str(obj.objid)))

    def get_object(self, objectid):
        with shelve.open(self.cache_path) as cache:
            return cache[objectid]

    def get_content(self, content_type):
        with shelve.open(self.cache_path) as cache:
            for objid, value in cache.items():
                try:
                    if value.content_type == content_type:
                        yield value
                except AttributeError:
                    logging.warning('Bad object returned from cache: {}'.format(value))
                    continue
