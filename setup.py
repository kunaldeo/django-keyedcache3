from setuptools import setup, find_packages

VERSION = (1, 5, 2)

# Dynamically calculate the version based on VERSION tuple
if len(VERSION)>2 and VERSION[2] is not None:
    str_version = "%d.%d.%s" % VERSION[:3]
else:
    str_version = "%d.%d" % VERSION[:2]

version= str_version

setup(
    name = 'django-keyedcache3',
    version = version,
    description = "keyedcache",
    long_description = """Python 3 version of Django Keyedcache provides utilities and class mixins for simplified development of cache-aware objects.  Used in Satchmo.""",
    author = 'Kunal Deo',
    author_email = 'kunaldeo@gmail.com',
    url = 'https://github.com/kunaldeo/django-keyedcache3',
    license = 'New BSD License',
    platforms = ['any'],
    classifiers = ['Development Status :: 4 - Beta',
                   'Environment :: Web Environment',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: BSD License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Programming Language :: Python :: 3.4',
                   'Programming Language :: Python :: 3.5',
                   'Framework :: Django'],
    packages = find_packages(),
    install_requires = ['django>=1.8'],
    include_package_data = True,
)
