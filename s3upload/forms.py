# -*- coding: utf-8 -*-
#
# Copyright 2014 Matt Austin
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from __future__ import absolute_import, unicode_literals
from . import settings
from datetime import datetime
from django import forms
from django.core.files.storage import default_storage
from hashlib import sha1
from magic import Magic
import hmac


class ContentTypePrefixMixin(object):

    content_type_prefix = ''  # e.g. 'image/', 'text/'

    def __init__(self, content_type_prefix=None, **kwargs):
        if content_type_prefix is not None:
            self.content_type_prefix = content_type_prefix
        return super(ContentTypePrefixMixin, self).__init__(**kwargs)

    def get_content_type_prefix(self):
        return self.content_type_prefix


class KeyPrefixMixin(object):

    upload_to = ''  # e.g. 'foo/bar/'

    def __init__(self, upload_to=None, **kwargs):
        if upload_to is not None:
            self.upload_to = upload_to
        return super(KeyPrefixMixin, self).__init__(**kwargs)

    def get_key_prefix(self):
        return ''.join([self.get_storage().location, self.upload_to])


class StorageMixin(object):

    def __init__(self, storage=None, **kwargs):
        self.storage = storage if storage is not None else default_storage
        return super(StorageMixin, self).__init__(**kwargs)

    def get_storage(self):
        return self.storage


class S3UploadForm(ContentTypePrefixMixin, KeyPrefixMixin, StorageMixin,
                   forms.Form):
    """Form for uploading a file directly to an S3 bucket."""

    access_key = forms.CharField(widget=forms.HiddenInput())

    acl = forms.CharField(widget=forms.HiddenInput())

    content_type = forms.CharField(widget=forms.HiddenInput())

    key = forms.CharField(widget=forms.HiddenInput())

    policy = forms.CharField(widget=forms.HiddenInput())

    success_action_redirect = forms.CharField(widget=forms.HiddenInput())

    success_action_status = forms.CharField(widget=forms.HiddenInput())

    signature = forms.CharField(widget=forms.HiddenInput())

    # http://docs.aws.amazon.com/AmazonS3/latest/dev/HTTPPOSTForms.html#HTTPPOSTFormFields
    # The file or content must be the last field rendered in the form.
    # Any fields below it are ignored.
    file = forms.FileField()

    expiration_timedelta = settings.EXPIRATION_TIMEDELTA

    field_name_overrides = {'content_type': 'Content-Type',
                            'access_key': 'AWSAccessKeyId'}

    success_action_status_code = 204

    def __init__(self, success_action_redirect=None, **kwargs):
        self._success_action_redirect = success_action_redirect
        super(S3UploadForm, self).__init__(**kwargs)
        self.fields['access_key'].initial = self.get_access_key()
        self.fields['acl'].initial = self.get_acl()
        self.fields['key'].initial = self.get_key()
        self.fields['policy'].initial = self.get_policy()
        self.fields['signature'].initial = self.get_signature()
        self.fields['success_action_status'].initial = \
            self.get_success_action_status_code()

        if not self.fields['content_type'].initial:
            self.fields['content_type'].initial = 'binary/octet-stream'

        # Only render success_action_redirect if a value is provided
        success_action_redirect = self.get_success_action_redirect()
        if success_action_redirect:
            self.fields['success_action_redirect'].initial = \
                success_action_redirect
        else:
            self.fields.pop('success_action_redirect')

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
        url = self.get_storage().url('')
        location = self.get_storage().location
        if url.endswith(location):
            url = url[:-len(location)]
        return url

    def get_bucket_name(self):
        return self.get_storage().bucket_name

    def get_conditions(self):
        conditions = [
            '{{"acl": "{0}"}}'.format(self.get_acl()),
            '{{"bucket": "{0}"}}'.format(self.get_bucket_name()),
            '["starts-with", "$Content-Type", "{0}"]'.format(
                self.get_content_type_prefix()),
            '["starts-with", "$key", "{0}"]'.format(self.get_key_prefix()),
            '["eq", "$success_action_status", "{0}"]'.format(
                self.get_success_action_status_code()),
        ]

        # Only render success_action_redirect if a value is provided
        success_action_redirect = self.get_success_action_redirect()
        if success_action_redirect:
            conditions += [
                '["eq", "$success_action_redirect", "{0}"]'.format(
                    success_action_redirect)
            ]

        return conditions

    def get_connection(self):
        return self.get_storage().connection

    def get_expiration_time(self, refresh=False):
        if not hasattr(self, '_expiration_time') and not refresh:
            expiration_datetime = datetime.now() + self.expiration_timedelta
            self._expiration_time = expiration_datetime.timetuple()
        return self._expiration_time

    def get_key(self):
        return '{0}${{filename}}'.format(self.get_key_prefix())

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

    def get_success_action_redirect(self):
        # http://docs.aws.amazon.com/AmazonS3/latest/dev/HTTPPOSTForms.html#HTTPPOSTConstructingPolicyRedirection
        return self._success_action_redirect

    def get_success_action_status_code(self):
        return self.success_action_status_code


class DropzoneS3UploadForm(S3UploadForm):

    success_action_status_code = 201

    class Media(object):
        css = {'all': ['s3upload/css/dropzone.css']}
        js = ['s3upload/dropzone.js', 's3upload/dropzone-options.js']


class ValidateS3UploadForm(ContentTypePrefixMixin, KeyPrefixMixin,
                           StorageMixin, forms.Form):
    """Form used to validate callback params."""

    bucket_name = forms.CharField(widget=forms.HiddenInput())

    etag = forms.CharField(widget=forms.HiddenInput())

    key_name = forms.CharField(widget=forms.HiddenInput())

    def _get_key(self):
        return self.get_storage().bucket.get_key(self.cleaned_data['key_name'])

    def clean(self):
        if self.cleaned_data.get('key_name') and self.cleaned_data.get('etag'):
            key = self._get_key()
            # Ensure key and etag match
            if not key.etag == self.cleaned_data['etag']:
                raise forms.ValidationError('Etag does not validate.')
            # Ensure content type starts with prefix
            if not key.content_type.startswith(self.get_content_type_prefix()):
                raise forms.ValidationError('Content-Type does not validate.')
        return self.cleaned_data

    def clean_bucket_name(self):
        # Ensure bucket in callback matches bucket name from storage
        bucket_name = self.cleaned_data['bucket_name']
        if not bucket_name == self.get_bucket_name():
            raise forms.ValidationError('Bucket name does not validate.')
        return bucket_name

    def clean_key_name(self):
        key = self.cleaned_data['key_name']
        # Ensure key starts with prefix
        if not key.startswith(self.get_key_prefix()):
            raise forms.ValidationError('Key does not have required prefix.')
        # Ensure key exists
        if not self._get_key():
            raise forms.ValidationError('Key does not exist.')
        return key

    def get_bucket_name(self):
        return self.get_storage().bucket_name

    def set_content_type(self):
        key = self._get_key()
        location = self.get_storage().location
        storage_path = self.cleaned_data['key_name'][len(location):]
        with self.get_storage().open(storage_path) as upload:
            content_type = Magic(mime=True).from_buffer(upload.read(1024))
        # TODO
        if not content_type.startswith(self.get_content_type_prefix()):
            raise forms.ValidationError('Content-Type does not validate.')
        key.update_metadata({b'Content-Type': b'{0}'.format(content_type)})
        key.copy(key.bucket.name, key.name, key.metadata, preserve_acl=True)
    set_content_type.alters_data = True
