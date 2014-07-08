from s3upload import __title__, __url__, __version__
from setuptools import setup
import os


def read(fname):
    # https://pythonhosted.org/an_example_pypi_project/setuptools.html#setting-up-setup-py
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name=__title__,
    version=__version__,
    description='Direct HTTP POST uploads to Amazon S3 with django-storages',
    author='Matt Austin',
    author_email='mail@mattaustin.me.uk',
    url=__url__,
    packages=['s3upload'],
    include_package_data=True,
    install_requires=['boto', 'django', 'django-storages'],
    long_description=read('README.rst'),
    keywords='s3,upload,post,django-storages,django',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
