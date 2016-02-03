[![Build Status](https://travis-ci.org/kunaldeo/django-keyedcache3.svg?branch=master)](https://travis-ci.org/kunaldeo/django-keyedcache3) [![PyPI version](https://badge.fury.io/py/django-keyedcache3.svg)](https://badge.fury.io/py/django-keyedcache3)

About
=====

Django-keyedcache provides a simplified, speedy way to manage caching in Django apps.

This is a Python 3 port of Django-keyedcache tested with Python 3.5.1 and Django 1.9.2.
This version has no threaded support.

Example
=======

The most frequent usage:

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
=================

More rare usage:

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
===============

All values of any slow function evaluated in the future can be cached transparently:

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

Optimizing to prevent concurrent multiple calculation of the same function value by concurrent processes is the main reason, why keyedcache is more complicated than could be expected.

Cache backend alias
===================
