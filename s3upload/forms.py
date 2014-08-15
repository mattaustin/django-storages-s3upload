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
from hashlib import md5, sha1
from magic import Magic
import hmac
import os


class ContentTypePrefixMixin(object):

    content_type_prefix = ''  # e.g. 'image/', 'text/'

    def __init__(self, content_type_prefix=None, **kwargs):
        if content_type_prefix is not None:
            self.content_type_prefix = content_type_prefix
        return super(ContentTypePrefixMixin, self).__init__(**kwargs)

    def get_content_type_prefix(self):
        return self.content_type_prefix


class KeyPrefixMixin(object):

    upload_to = 'incoming/'  # e.g. 'foo/bar/'

    def __init__(self, upload_to=None, **kwargs):
        if upload_to is not None:
            self.upload_to = upload_to
        return super(KeyPrefixMixin, self).__init__(**kwargs)

    def get_key_prefix(self):
        return os.path.join(self.get_storage().location, self.upload_to)


class StorageMixin(object):

    def __init__(self, storage=None, **kwargs):
        self.storage = storage if storage is not None else default_storage
        return super(StorageMixin, self).__init__(**kwargs)

    def get_bucket_name(self):
        return self.get_storage().bucket_name

    def get_storage(self):
        return self.storage


class S3UploadForm(ContentTypePrefixMixin, KeyPrefixMixin, StorageMixin,
                   forms.Form):
    """Form for uploading a file directly to an S3 bucket."""

    access_key = forms.CharField(widget=forms.HiddenInput())

    acl = forms.CharField(widget=forms.HiddenInput())

    cache_control = forms.CharField(widget=forms.HiddenInput())

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

    field_name_overrides = {'cache_control': 'Cache-Control',
                            'content_type': 'Content-Type',
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

        # Only render Cache-Control if a value is provided
        cache_control = self.get_cache_control()
        if cache_control:
            self.fields['cache_control'].initial = cache_control
        else:
            self.fields.pop('cache_control')

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
        """Return the acl to be set on the uploaded file.

        By default this sets a 'private' acl, and should probably be kept that
        way. You can set the final acl when the upload is validated/processed.

        """

        return 'private'

    def get_action(self):
        url = self.get_storage().url('')
        location = self.get_storage().location
        if location and url.endswith(location):
            url = url[:-len(location)]
        return url

    def get_cache_control(self):
        return self.get_storage().headers.get('Cache-Control', '')

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

        # Only render Cache-Control if a value is provided
        cache_control = self.get_cache_control()
        if cache_control:
            conditions += [
                '["eq", "$Cache-Control", "{0}"]'.format(cache_control)
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
            expiration_datetime = datetime.utcnow() + self.expiration_timedelta
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
    """Form for uploading a file directly to an S3 bucket using dropzone.js."""

    success_action_status_code = 201

    class Media(object):
        css = {'all': ['s3upload/css/dropzone.css']}
        js = ['s3upload/dropzone.js', 's3upload/dropzone-options.js']


class ValidateS3UploadForm(ContentTypePrefixMixin, KeyPrefixMixin,
                           StorageMixin, forms.Form):
    """Form used to validate returned data from S3.

    Not for use in templates - we're only processing/validating the provided
    data.

    """

    bucket_name = forms.CharField(widget=forms.HiddenInput())
    """Name of the S3 bucket."""

    etag = forms.CharField(widget=forms.HiddenInput())
    """Etag of the uploaded file."""

    key_name = forms.CharField(widget=forms.HiddenInput())
    """Key name (path) of the uploaded file."""

    process_to = 'processed/'  # e.g. 'foo/bar/'
    """Path to place processed files in."""

    def __init__(self, process_to=None, **kwargs):
        if process_to is not None:
            self.process_to = process_to
        return super(ValidateS3UploadForm, self).__init__(**kwargs)

    def clean(self):
        if self.cleaned_data.get('key_name') and self.cleaned_data.get('etag'):
            key = self.get_upload_key()
            # Ensure key and etag match
            if not key.etag == self.cleaned_data['etag']:
                raise forms.ValidationError('Etag does not validate.')
            # Ensure initial content type starts with prefix
            if not key.content_type.startswith(self.get_content_type_prefix()):
                raise forms.ValidationError('Content-Type does not validate.')
            # Ensure actual content type starts with prefix
            content_type = self.get_processed_content_type()
            if not content_type.startswith(self.get_content_type_prefix()):
                raise forms.ValidationError('Content-Type does not validate.')
        return self.cleaned_data

    def clean_bucket_name(self):
        """Validates that the bucket name in the provided data matches the
        bucket name from the storage backend."""
        bucket_name = self.cleaned_data['bucket_name']
        if not bucket_name == self.get_bucket_name():
            raise forms.ValidationError('Bucket name does not validate.')
        return bucket_name

    def clean_key_name(self):
        """Validates that the key in the provided data starts with the
        required prefix, and that it exists in the bucket."""
        key = self.cleaned_data['key_name']
        # Ensure key starts with prefix
        if not key.startswith(self.get_key_prefix()):
            raise forms.ValidationError('Key does not have required prefix.')
        # Ensure key exists
        if not self.get_upload_key():
            raise forms.ValidationError('Key does not exist.')
        return key

    def get_processed_acl(self):
        """Return the acl to be set on the processed file."""
        return self.get_storage().default_acl

    def get_processed_content_type(self):
        """Determine the actual content type of the upload."""
        if not hasattr(self, '_processed_content_type'):
            with self.get_storage().open(self.get_upload_path()) as upload:
                content_type = Magic(mime=True).from_buffer(upload.read(1024))
            self._processed_content_type = content_type
        return self._processed_content_type

    def get_processed_key_name(self):
        """Return the full path to use for the processed file."""
        name = self.get_upload_key().name
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        extension = '.{0}'.format(name.split('.')[-1]) if '.' in name else ''
        digest = md5(''.join([timestamp, name])).hexdigest()
        return os.path.join(self.get_storage().location, self.process_to,
                            '{0}{1}'.format(digest, extension))

    def process_upload(self, set_content_type=True):
        """Process the uploaded file."""
        metadata = self.get_upload_key_metadata()

        if set_content_type:
            content_type = self.get_processed_content_type()
            metadata.update({b'Content-Type': b'{0}'.format(content_type)})

        upload_key = self.get_upload_key()
        processed_key_name = self.get_processed_key_name()
        processed_key = upload_key.copy(upload_key.bucket.name,
                                        processed_key_name, metadata)
        processed_key.set_acl(self.get_processed_acl())
        upload_key.delete()
    process_upload.alters_data = True

    def get_upload_key(self):
        """Get the `Key` from the S3 bucket for the uploaded file.

        :returns: Key (object) of the uploaded file.
        :rtype: :py:class:`boto.s3.key.Key`

        """

        if not hasattr(self, '_upload_key'):
            self._upload_key = self.get_storage().bucket.get_key(
                self.cleaned_data['key_name'])
        return self._upload_key

    def get_upload_key_metadata(self):
        """Generate metadata dictionary from a bucket key."""
        key = self.get_upload_key()
        metadata = key.metadata.copy()

        # Some http header properties which are stored on the key need to be
        # copied to the metadata when updating
        headers = {
            # http header name, key attribute name
            'Cache-Control': 'cache_control',
            'Content-Type': 'content_type',
            'Content-Disposition': 'content_disposition',
            'Content-Encoding': 'content_encoding',
        }

        for header_name, attribute_name in headers.items():
            attribute_value = getattr(key, attribute_name, False)
            if attribute_value:
                metadata.update({b'{0}'.format(header_name):
                                 b'{0}'.format(attribute_value)})
        return metadata

    def get_upload_path(self):
        """Returns the uploaded file path from the storage backend.

        :returns: File path from the storage backend.
        :rtype: :py:class:`unicode`

        """
        location = self.get_storage().location
        return self.cleaned_data['key_name'][len(location):]
