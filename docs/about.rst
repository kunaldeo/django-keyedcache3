About
-----

Django-keyedcache provides a simplified, speedy way to manage caching in Django apps.

Example
-------
The most frequent usage:

    import keyedcache import cache_set, cache_get, NotCachedError
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
More rare usage:

    # it is better sometimes to call the internal function `cache_key` to
    # combine complicated parameters to one key used multiple times0.
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

Additional first-level caching
------------------------------

If you want first to cache the values temporary in the memory during one request
before the normal django cache.

    from keyedcache import threaded
    threaded.start_listening()

This should be safe also with multithreading.


Web interface
-------------

Cache statistics, cached keys and deleting the cache can be accessed by running the dev
server in the test_app directory and going to `settings <http://127.0.0.1:8000/cache/>`_ ::

(Urls of in keyedcache are usually mapped to "/cache" by the main application.)
The web intergace is for debugging purposes and usage with debug server.
If the server is running in production with multiple worker processes,
the information provided by the web interface is incomplete. The access
to the web interface requires "is_staff" permissions.
