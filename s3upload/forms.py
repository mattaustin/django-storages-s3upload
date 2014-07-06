# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from datetime import datetime, timedelta
from django import forms
from django.core.files.storage import default_storage
from hashlib import sha1
import base64
import hmac
import time


class S3UploadForm(forms.Form):
    """Form for uploading a file directly to an S3 bucket."""

    access_key = forms.CharField(widget=forms.HiddenInput())

    key = forms.CharField(widget=forms.HiddenInput())

    acl = forms.CharField(widget=forms.HiddenInput())

    policy = forms.CharField(widget=forms.HiddenInput())

    signature = forms.CharField(widget=forms.HiddenInput())

    content_type = forms.CharField(widget=forms.HiddenInput())

    # http://docs.aws.amazon.com/AmazonS3/latest/dev/HTTPPOSTForms.html#HTTPPOSTFormFields
    # The file or content must be the last field rendered in the form.
    # Any fields below it are ignored.
    file = forms.FileField()

    content_type_prefix = '' # e.g. 'image/', 'text/'

    expiration_timedelta = timedelta(minutes=20)

    field_name_overrides = {'content_type': 'Content-Type',
                            'access_key': 'AWSAccessKeyId'}

    upload_to = '' # e.g. 'foo/bar/'

    storage = default_storage

    def __init__(self, *args, **kwargs):
        super(S3UploadForm, self).__init__(*args, **kwargs)
        self.fields['access_key'].initial = self.get_access_key()
        self.fields['key'].initial = self.get_key()
        self.fields['acl'].initial = self.get_acl()
        self.fields['policy'].initial = self.get_policy()
        self.fields['signature'].initial = self.get_signature()
        self.fields['content_type'].initial = 'binary/octet-stream' #TODO

    def _base64_encode(self, string):
        return string.encode('base64').replace('\n', '')

    def add_prefix(self, field_name):
        # Here we abuse the add_prefix method in order to override the input
        # names of certain fields which require non-pythonic names.
        # http://stackoverflow.com/questions/8801910/override-django-form-fields-name-attr
        field_name = self.field_name_overrides.get(field_name, field_name)
        return super(S3UploadForm, self).add_prefix(field_name)

    def get_access_key(self):
        return self.get_storage().access_key

    def get_acl(self):
        return self.get_storage().default_acl

    def get_action(self):
        # TODO: Can we get the full url from storage instead of reconstructing
        # it? What if the storage already has a prefix specified?
        return 'https://{0}.s3.amazonaws.com/'.format(self.get_bucket_name())

    def get_bucket_name(self):
        return self.get_storage().bucket_name

    def get_callback_url(self):
        # TODO: Callback url
        raise NotImplementedError()

    def get_conditions(self):
        return [
            '{{"acl": "{0}"}}'.format(self.get_acl()),
            '{{"bucket": "{0}"}}'.format(self.get_bucket_name()),
            '["starts-with", "$key", "{0}"]'.format(self.get_key_prefix()),
            '["starts-with", "$Content-Type", "{0}"]'.format(
                self.get_content_type_prefix()),
        ]

    def get_connection(self):
        return self.get_storage().connection

    def get_content_type_prefix(self):
        return self.content_type_prefix

    def get_expiration_time(self, refresh=False):
        if not hasattr(self, '_expiration_time') and not refresh:
            expiration_datetime = datetime.now() + self.expiration_timedelta
            self._expiration_time = expiration_datetime.timetuple()
        return self._expiration_time

    def get_key(self):
        return '{0}${{filename}}'.format(self.get_key_prefix())

    def get_key_prefix(self):
        return self.upload_to

    def get_policy(self):
        # http://docs.aws.amazon.com/AmazonS3/latest/dev/HTTPPOSTForms.html#HTTPPOSTConstructPolicy
        connection = self.get_connection()
        policy = connection.build_post_policy(self.get_expiration_time(),
                                              self.get_conditions())
        return self._base64_encode(policy.replace('\n', '').encode('utf-8'))

    def get_signature(self):
        # http://docs.aws.amazon.com/AmazonS3/latest/dev/HTTPPOSTForms.html#HTTPPOSTConstructingPolicySignature
        digest = hmac.new(self.get_secret_key().encode('utf-8'),
                          self.get_policy(), sha1).digest()
        return self._base64_encode(digest)

    def get_secret_key(self):
        return self.get_storage().secret_key

    def get_storage(self):
        return self.storage
