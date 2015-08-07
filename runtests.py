# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.conf import settings
from django.test.utils import get_runner
import django
import sys


def run_tests(test_args):

    if not test_args:
        test_args = ['tests']

    settings.configure(
        DEBUG=True,
        SECRET_KEY='fake-key',
        INSTALLED_APPS=[
            's3upload',
            'storages',
        ],
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
            }
        },
        USE_TZ=True
    )

    try:
        django.setup()
    except AttributeError:
        pass

    TestRunner = get_runner(settings)
    test_runner = TestRunner()

    failures = test_runner.run_tests(test_args)

    sys.exit(bool(failures))


if __name__ == '__main__':
    test_args = sys.argv[1:]
    run_tests(test_args)
