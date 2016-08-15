# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.conf import settings
from django.test.utils import get_runner
import django
import sys


def run_tests(**test_args):

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

    if not test_args:
        test_args = ['tests']

    TestRunner = get_runner(settings)
    test_runner = TestRunner()

    failures = test_runner.run_tests(test_args)

    if failures:
        sys.exit(bool(failures))


if __name__ == '__main__':
    run_tests(*sys.argv[1:])
