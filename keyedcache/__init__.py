"""A full cache system written on top of Django's rudimentary one.

Frequently used functions are:
    cache_set(*keys, **kwargs)
    cache_get(*keys, **kwargs)
    cache_delete(*keys, **kwargs)
keys.. parameters of general type which are convertable to string or hashable unambiguously.
The keys can be of any general type which is convertable to string unambiguously or hashable.
Every unknown kwarg is interpreted like two aditional keys: (key, val).
Example:
    cache_set('product', 123, value=product)
    # is the same as
    cache_set('product::123', value=product)

More info below about parameters.
"""
# For keyedcache developers:
# No additional keyword parameters should be added to the definition of
# cache_set, cache_get, cache_delete or cache_key in the future.
# Otherwise you must know what are you doing! Any appplication that would use
# a new parameter will must check on startup that keyedcache is not older than
# a required version !!(Otherwise kwargs unknown by an old version keyedcache
# will be used as keys and cache_set/cache_get will use different keys that
# would cause serious problems.)

from django.conf import settings
from django.core.cache import caches, InvalidCacheBackendError, DEFAULT_CACHE_ALIAS
from django.core.exceptions import ImproperlyConfigured
from django.utils.encoding import smart_str
from hashlib import md5
from keyedcache.utils import is_string_like, is_list_or_tuple
from warnings import warn
import cPickle as pickle
import logging
import types

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
log.addHandler(logging.NullHandler())

# The debugging variable CACHED_KEYS is exact only with the the Django
# debugging server (or any single worker process server) and without restarting
# the server between restarts of the main cache (memcached).
# Keys in CACHED_KEYS variable never expire and can eat much memory on long
# running servers. Currently it is not confirmed in Satchmo.
# If more worker processes are used, the reported values of the following three
# variables can skip randomly upwards downwards.
CACHED_KEYS = {}
CACHE_CALLS = 0
CACHE_HITS = 0

KEY_DELIM = "::"
REQUEST_CACHE = {'enabled' : False}

cache, cache_alias, CACHE_TIMEOUT, _CACHE_ENABLED = 4 * (None,)


def keyedcache_configure():
    "Initial configuration (or reconfiguration during tests)."
    global cache, cache_alias, CACHE_TIMEOUT, _CACHE_ENABLED
    cache_alias = getattr(settings, 'KEYEDCACHE_ALIAS', DEFAULT_CACHE_ALIAS)
    try:
        cache = caches[cache_alias]
    except InvalidCacheBackendError:
        log.warn("Warning: Could not find backend '%s': uses %s" % (cache_alias, DEFAULT_CACHE_ALIAS))
        cache_alias = DEFAULT_CACHE_ALIAS  # it is 'default'
        from django.core.cache import cache


    CACHE_TIMEOUT = cache.default_timeout
    if CACHE_TIMEOUT == 0:
        log.warn("disabling the cache system because TIMEOUT=0")
        
    _CACHE_ENABLED = CACHE_TIMEOUT > 0 and not cache.__module__.endswith('dummy')

    if not cache.key_prefix and (hasattr(settings, 'CACHE_PREFIX') or settings.SITE_ID != 1):
        if hasattr(settings, 'CACHE_PREFIX'):
            warn("The setting `CACHE_PREFIX` is obsoleted and is ignored by keyedcache.\n"
                 """Use "CACHES = {'default': {... 'KEY_PREFIX': '...'}}" instead.""")
        if settings.SITE_ID != 1:
            hint = ("Use \"CACHES = {'default': {... 'KEY_PREFIX': '...'}}\" in order to\n"
                    "differentiate caches or to explicitely confirm they should be shared.\n"
                    " An easy solution is \"'CACHE_PREFIX': str(settings.SITE_ID)\".")
            warn("An explicit KEY_PREFIX should be defined if you use multiple sites.\n%s" % hint)
        if not cache.__module__.split('.')[-1] in ('locmem', 'dummy'):
            raise ImproperlyConfigured(
                    "Setting KEY_PREFIX is obligatory for production caches. See the previous warning.")

keyedcache_configure()


class CacheWrapper(object):
    def __init__(self, val, inprocess=False):
        self.val = val
        self.inprocess = inprocess

    def __str__(self):
        return str(self.val)

    def __repr__(self):
        return repr(self.val)

    def wrap(cls, obj):
        if isinstance(obj, cls):
            return obj
        else:
            return cls(obj)

    wrap = classmethod(wrap)

class MethodNotFinishedError(Exception):
    def __init__(self, f):
        self.func = f


class NotCachedError(Exception):
    def __init__(self, k):
        self.key = k

class CacheNotRespondingError(Exception):
    pass

def cache_delete(*keys, **kwargs):
    """
    Deletes the object identified by all ``keys`` from the cache.

    keys:
        Parameters of general type which are convertable to string or hashable
        unambiguously.
    kwargs:
        children:
            If it is True more objects starting with these keys are deleted.
        other kwargs:
            Unknown key=val is interpreted like two aditional keys: (key, val)

    If no keys are present, all cached objects are to be deleted.
    Deleting multiple multiple or all objects is usually not complete if the
    project is running with multiple worker processes.
    (It is reliable e.g. with a development server.)
    """
    removed = []
    if cache_enabled():
        global CACHED_KEYS
        log.debug('cache_delete')
        children = kwargs.pop('children', False)

        if (keys or kwargs):
            key = cache_key(*keys, **kwargs)

            if CACHED_KEYS.has_key(key):
                del CACHED_KEYS[key]
                removed.append(key)

            cache.delete(key)

            if children:
                key = key + KEY_DELIM
                children = [x for x in CACHED_KEYS.keys() if x.startswith(key)]
                for k in children:
                    del CACHED_KEYS[k]
                    cache.delete(k)
                    removed.append(k)
        else:
            key = "All Keys"
            deleteneeded = _cache_flush_all()

            removed = CACHED_KEYS.keys()

            if deleteneeded:
                for k in CACHED_KEYS:
                    cache.delete(k)

            CACHED_KEYS = {}

        if removed:
            log.debug("Cache delete: %s", removed)
        else:
            log.debug("No cached objects to delete for %s", key)

    return removed


def cache_delete_function(func):
    return cache_delete(['func', func.__name__, func.__module__], children=True)

def cache_enabled():
    global _CACHE_ENABLED
    return _CACHE_ENABLED

def cache_enable(state=True):
    global _CACHE_ENABLED
    _CACHE_ENABLED=state

def _cache_flush_all():
    if is_memcached_backend():
        cache._cache.flush_all()
        return False
    return True

def cache_function(length=CACHE_TIMEOUT):
    """
    A variant of the snippet posted by Jeff Wheeler at
    http://www.djangosnippets.org/snippets/109/

    Caches a function, using the function and its arguments as the key, and the return
    value as the value saved. It passes all arguments on to the function, as
    it should.

    The decorator itself takes a length argument, which is the number of
    seconds the cache will keep the result around.

    It will put a temp value in the cache while the function is
    processing. This should not matter in most cases, but if the app is using
    threads, you won't be able to get the previous value, and will need to
    wait until the function finishes. If this is not desired behavior, you can
    remove the first two lines after the ``else``.
    """
    def decorator(func):
        def inner_func(*args, **kwargs):
            if not cache_enabled():
                value = func(*args, **kwargs)

            else:
                try:
                    value = cache_get('func', func.__name__, func.__module__, args, kwargs)

                except NotCachedError, e:
                    # This will set a temporary value while ``func`` is being
                    # processed. When using threads, this is vital, as otherwise
                    # the function can be called several times before it finishes
                    # and is put into the cache.
                    funcwrapper = CacheWrapper(".".join([func.__module__, func.__name__]), inprocess=True)
                    cache_set(e.key, value=funcwrapper, length=length, skiplog=True)
                    value = func(*args, **kwargs)
                    cache_set(e.key, value=value, length=length)

                except MethodNotFinishedError, e:
                    value = func(*args, **kwargs)

            return value
        return inner_func
    return decorator


def cache_get(*keys, **kwargs):
    """
    Gets the object identified by all ``keys`` from the cache.

    kwargs:
        default:
            Default value used if the object is not in the cache. If the object
            is not found and ``default`` is not set or is None, the exception
            ``NotCachedError`` is raised with the attribute ``.key = keys``.
        other kwargs:
            Unknown key=val is interpreted like two aditional keys: (key, val)
    """
    if kwargs.has_key('default'):
        default_value = kwargs.pop('default')
        use_default = True
    else:
        use_default = False

    key = cache_key(keys, **kwargs)

    if not cache_enabled():
        raise NotCachedError(key)
    else:
        global CACHE_CALLS, CACHE_HITS, REQUEST_CACHE
        CACHE_CALLS += 1
        if CACHE_CALLS == 1:
            cache_require()

        obj = None
        tid = -1
        if REQUEST_CACHE['enabled']:
            tid = cache_get_request_uid()
            if tid > -1:
                try:
                    obj = REQUEST_CACHE[tid][key]
                    log.debug('Got from request cache: %s', key)
                except KeyError:
                    pass

        if obj == None:
            obj = cache.get(key)

        if obj and isinstance(obj, CacheWrapper):
            CACHE_HITS += 1
            CACHED_KEYS[key] = True
            log.debug('got cached [%i/%i]: %s', CACHE_CALLS, CACHE_HITS, key)
            if obj.inprocess:
                raise MethodNotFinishedError(obj.val)

            cache_set_request(key, obj, uid=tid)

            return obj.val
        else:
            try:
                del CACHED_KEYS[key]
            except KeyError:
                pass

            if use_default:
                return default_value

            raise NotCachedError(key)


def cache_set(*keys, **kwargs):
    """Set the object identified by all ``keys`` into the cache.

    kwargs:
        value:
            The object to be cached.
        length:
            Timeout for the object. Default is CACHE_TIMEOUT.
        skiplog:
            If it is True the call is never logged. Default is False.
        other kwargs:
            Unknown key=val is interpreted like two aditional keys: (key, val)
    """
    if cache_enabled():
        global CACHED_KEYS, REQUEST_CACHE
        obj = kwargs.pop('value')
        length = kwargs.pop('length', CACHE_TIMEOUT)
        skiplog = kwargs.pop('skiplog', False)

        key = cache_key(keys, **kwargs)
        val = CacheWrapper.wrap(obj)
        if not skiplog:
            log.debug('setting cache: %s', key)
        cache.set(key, val, length)
        CACHED_KEYS[key] = True
        if REQUEST_CACHE['enabled']:
            cache_set_request(key, val)

def _hash_or_string(key):
    if is_string_like(key) or isinstance(key, (types.IntType, types.LongType, types.FloatType)):
        return smart_str(key)
    else:
        try:
            #if it has a PK, use it.
            return str(key._get_pk_val())
        except AttributeError:
            return md5_hash(key)

def cache_key(*keys, **pairs):
    """Smart key maker, returns the object itself if a key, else a list
    delimited by ':', automatically hashing any non-scalar objects."""

    if len(keys) == 1 and is_list_or_tuple(keys[0]):
        keys = keys[0]

    if pairs:
        keys = list(keys)
        for k in sorted(pairs.keys()):
            keys.extend((k, pairs[k]))

    key = KEY_DELIM.join([_hash_or_string(x) for x in keys])
    return key.replace(" ", ".")

def md5_hash(obj):
    pickled = pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)
    return md5(pickled).hexdigest()


def is_memcached_backend():
    try:
        return cache._cache.__module__.endswith('memcache')
    except AttributeError:
        return False

def cache_require():
    """Error if keyedcache isn't running."""
    if cache_enabled():
        key = cache_key('require_cache')
        cache_set(key,value='1')
        v = cache_get(key, default = '0')
        if v != '1':
            raise CacheNotRespondingError()
        else:
            log.debug("Cache responding OK")
        return True

def cache_clear_request(uid):
    """Clears all locally cached elements with that uid"""
    global REQUEST_CACHE
    try:
        del REQUEST_CACHE[uid]
        log.debug('cleared request cache: %s', uid)
    except KeyError:
        pass

def cache_use_request_caching():
    global REQUEST_CACHE
    REQUEST_CACHE['enabled'] = True

def cache_get_request_uid():
    from threaded_multihost import threadlocals
    return threadlocals.get_thread_variable('request_uid', -1)

def cache_set_request(key, val, uid=None):
    if uid == None:
        uid = cache_get_request_uid()

    if uid>-1:
        global REQUEST_CACHE
        if not uid in REQUEST_CACHE:
            REQUEST_CACHE[uid] = {key:val}
        else:
            REQUEST_CACHE[uid][key] = val
