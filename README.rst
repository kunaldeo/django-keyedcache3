About
-----

Django-keyedcache provides a simplified, speedy way to manage caching in Django apps.

Example
-------
The most frequent usage::

    from keyedcache import cache_set, cache_get, NotCachedError
    import keyedcache

    # ... create come object
    # cache it
    cache_set("product", 123, value=product)
    cache_set("product", 123, value=product, length=3600)  # different timeout
    # ... delete it
    # get it
    try:
        value = cache_get("product", 123)
    except NotCachedError:
        value = None

    # the syntax "parameter=var" does exactly the same as the previous:
    try:
        value = cache_get(product=123)
    ....

    # optional deleting
    keyedcache.cache_delete('some.temporary.secret')

The reference documentation for these functions is their docs strings.

Advanced examples
-----------------
More rare usage::

    # it is better sometimes to call the internal function `cache_key` to
    # combine complicated parameters to one key used multiple times.
    cachekey = keyedcache.cache_key('SHIP_company', \
            weight=str(weight), country=country.code, zipcode=zipcode)
    try:
        value = cache_get(cachekey)
    except NotCachedError:
        value = None
    if value == None:
        value = ...long running function...
        cache_set(cachekey, value=value)
        log.info('message %s', cachekey)

    ...

    # Mixin - for models.py - simplified caching for some model
    class MyNewModel(models.Model, keyedcache.CachedObjectMixin):
        # some Fields...

        # we can easy cache saving of all objects without writing the keys
        def save(self):
            # ... do somehting
            self.cache_delete()
            super(MyNewModel, self).save()
            self.cache_set()
            return self


Cached function
---------------

All values of any slow function evaluated in the future can be cached transparently::

    import keyedcache
    from time import sleep

    def nearest_restaurant(gps_x, gps_y):
       sleep(3)   # internet
       return 'Havana Road' if (gps_x -3) ** 2 + (gps_y - 6) ** 2 <= 1 else 'unknown'

    cached_restaurant = keyedcache.cache_function(60)(nearest_restaurant)
    print cached_restaurant( 2, 6)  # slow
    print cached_restaurant(-3, 4)  # slow
    print cached_restaurant( 2, 6)  # fast
    keyedcache.cache_delete_function(nearest_restaurant)
    print cached_restaurant( 2, 6)  # slow

Optimizing to prevent concurrent multiple calculation of the same function
value by concurrent processes is the main reason, why keyedcache is more
complicated than could be expected.


Additional first-level caching
------------------------------

If you want first to cache the values temporary in the memory during one request
before the normal django cache::

    from keyedcache import threaded
    threaded.start_listening()

This should be safe also with multithreading.


Cache backend alias
-------------------

The backend used by cache can be selected by settings variable `KEYEDCACHE_ALIAS`
if the project uses more backends. The default is 'default'.

Web interface
-------------

Cache statistics, cached keys and deleting the cache can be accessed by running the dev
server in the test_app directory and going to settings http://127.0.0.1:8000/cache/.

(Urls of in keyedcache are usually mapped to "/cache" by the main application.)
The web intergace is for debugging purposes and usage with debug server.
If the server is running in production with multiple worker processes,
the information provided by the web interface is incomplete. The access
to the web interface requires "is_staff" permissions.

Requirements
------------

Python 2.5, 2.6 or 2.7; Django 1.4 or 1.5

(optional) If you want to use the threaded first-level cache, you need to install `threaded_multihost`_.

It is recommended to set a 'KEY_PREFIX' to any unique string in your settings.py file.
For production caches or for sites with different values SITE_ID it is even obligatory.
This allows you to avoid collisions when running more than one site with the same backend.
An easy solution is `CACHES = {'defalt': {... 'KEY_PREFIX': str(settings.SITE_ID)}}`.

.. _`threaded_multihost`: http://bitbucket.org/bkroeze/django-threaded-multihost/

Release notes
-------------
ver. 1.5.0

* The cache configuration is made compatible with current versions of Django.
It is currently configured by the varible CACHES. The variable CACHE_PREFIX
is currently obsoleted 
CACHES.
