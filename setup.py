from setuptools import setup, find_packages

version = __import__('keyedcache').__version__

setup(
    name = 'django-keyedcache',
    version = version,
    description = "keyedcache",
    long_description = """Django Keyedcache provides utilities and class mixins for simplified development of cache-aware objects.  Used in Satchmo.""",
    author = 'Bruce Kroeze',
    author_email = 'brucek@ecomsmith.com',
    url = 'http://bitbucket.org/bkroeze/django-keyedcache/',
    license = 'New BSD License',
    platforms = ['any'],
    classifiers = ['Development Status :: 4 - Beta',
                   'Environment :: Web Environment',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: BSD License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Framework :: Django'],
    packages = find_packages(),
    include_package_data = True,
)
