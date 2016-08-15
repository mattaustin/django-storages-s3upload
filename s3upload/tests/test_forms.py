# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.core.files.storage import Storage
from django.forms import Form
from django.test import TestCase
from django.utils.encoding import smart_str
from s3upload import forms
from storages.backends.s3boto import S3BotoStorage
import unittest


try:  # Python 3
    from unittest import mock
except ImportError:  # Python 2
    import mock


class TestContentTypePrefixMixin(TestCase):

    def setUp(self):
        class FormWithContentTypePrefixMixin(forms.ContentTypePrefixMixin,
                                             Form):
            pass

        self.FormWithContentTypePrefixMixin = FormWithContentTypePrefixMixin

    # __init__

    def test_content_type_prefix_is_set_if_provided(self):
        test_content_type_prefix = 'x-test/'
        form = self.FormWithContentTypePrefixMixin(
            content_type_prefix=test_content_type_prefix)
        self.assertEqual(form.content_type_prefix, test_content_type_prefix)

    def test_content_type_prefix_is_set_to_class_default_if_not_provided(self):
        form = self.FormWithContentTypePrefixMixin()
        self.assertEqual(
            form.content_type_prefix,
            self.FormWithContentTypePrefixMixin.content_type_prefix)

    # get_content_type_prefix

    def test_get_content_type_prefix_returns_set_content_type_prefix(self):
        form = self.FormWithContentTypePrefixMixin(
            content_type_prefix='x-test/')
        self.assertEqual(form.get_content_type_prefix(),
                         form.content_type_prefix)


class TestKeyPrefixMixin(TestCase):

    def setUp(self):
        class FormWithKeyPrefixMixin(forms.KeyPrefixMixin, Form):
            pass

        self.FormWithKeyPrefixMixin = FormWithKeyPrefixMixin

    # __init__

    def test_upload_to_is_set_if_provided(self):
        test_upload_to = 'TEST/'
        form = self.FormWithKeyPrefixMixin(upload_to=test_upload_to)
        self.assertEqual(form.upload_to, test_upload_to)

    def test_upload_to_is_set_to_class_default_if_not_provided(self):
        form = self.FormWithKeyPrefixMixin()
        self.assertEqual(form.upload_to, self.FormWithKeyPrefixMixin.upload_to)

    # get_key_prefix

    @unittest.skip('Not implemented.')
    def test_get_key_prefix_joins_storage_location_with_upload_to(self):
        # TODO
        # https://joeray.me/mocking-files-and-file-storage-for-testing-django-models.html
        # "We need to patch _wrapped because default_storage is a lazy-loaded
        # object and _wrapped is the property which it uses to determine
        # if it’s been loaded yet or not."
        # default_storage_mock = mock.MagicMock(spec=Storage)
        # with mock.patch('django.core.files.storage.default_storage._wrapped',
        #                 default_storage_mock):
        #     form = self.FormWithStorageMixin()
        #     self.assertEqual(form.storage, default_storage_mock)

        # Code to test:
        # return os.path.join(self.get_storage().location, self.upload_to)

        raise NotImplementedError()


class TestStorageMixin(TestCase):

    def setUp(self):
        class FormWithStorageMixin(forms.StorageMixin, Form):
            pass

        self.FormWithStorageMixin = FormWithStorageMixin

    # __init__

    def test_storage_is_set_if_provided(self):
        test_storage = mock.MagicMock(spec=Storage)
        form = self.FormWithStorageMixin(storage=test_storage)
        self.assertEqual(form.storage, test_storage)

    def test_default_storage_is_set_to_default_if_not_provided(self):
        default_storage_mock = mock.MagicMock(spec=Storage)
        # https://joeray.me/mocking-files-and-file-storage-for-testing-django-models.html
        # "We need to patch _wrapped because default_storage is a lazy-loaded
        # object and _wrapped is the property which it uses to determine
        # if it’s been loaded yet or not."
        with mock.patch('django.core.files.storage.default_storage._wrapped',
                        default_storage_mock):
            form = self.FormWithStorageMixin()
            self.assertEqual(form.storage, default_storage_mock)

    # get_bucket_name

    def test_get_bucket_name_returns_storage_bucket_name(self):
        test_storage = mock.MagicMock(spec=Storage,
                                      bucket_name='TEST_STORAGE_BUCKET_NAME')
        form = self.FormWithStorageMixin(storage=test_storage)
        self.assertEqual(form.get_bucket_name(), test_storage.bucket_name)

    # get_connection

    def test_get_connection_returns_storage_connection(self):
        test_storage = mock.MagicMock(spec=Storage,
                                      connection='TEST_STORAGE_CONNECTION')
        form = self.FormWithStorageMixin(storage=test_storage)
        self.assertEqual(form.get_connection(), test_storage.connection)

    # get_storage

    def test_get_storage_returns_set_storage(self):
        test_storage = mock.MagicMock(spec=Storage)
        form = self.FormWithStorageMixin(storage=test_storage)
        self.assertEqual(form.get_storage(), form.storage)


class TestS3UploadForm(TestCase):

    def setUp(self):
        self.storage_mock = mock.MagicMock(spec=S3BotoStorage,
                                           access_key='TEST_ACCESS_KEY',
                                           secret_key='TEST_SECRET_KEY')

        # A lot of these tests require a form with a mocked get_policy.
        self.S3UploadFormWithMockPolicy = type(
            smart_str('S3UploadFormWithMockPolicy'), (forms.S3UploadForm,),
            {'get_policy': mock.Mock(return_value='TEST_POLICY')})

    # __init__  # TODO

    def test_success_action_redirect_is_set_if_provided(self):
        test_success_action_redirect = 'TEST_SUCCESS_ACTION_REDIRECT'
        form = self.S3UploadFormWithMockPolicy(
            storage=self.storage_mock,
            success_action_redirect=test_success_action_redirect)
        self.assertEqual(form._success_action_redirect,
                         test_success_action_redirect)

    def test_success_action_redirect_is_none_if_not_provided(self):
        form = self.S3UploadFormWithMockPolicy(storage=self.storage_mock)
        self.assertIsNone(form._success_action_redirect)

    def test_access_key_is_set_as_field_initial_value_on_init(self):
        form = self.S3UploadFormWithMockPolicy(storage=self.storage_mock)
        self.assertEqual(form.fields['access_key'].initial,
                         self.storage_mock.access_key)

    def test_acl_is_set_as_field_initial_value_on_init(self):
        form = self.S3UploadFormWithMockPolicy(storage=self.storage_mock)
        self.assertEqual(form.fields['acl'].initial, form.get_acl())

    def test_policy_is_set_as_field_initial_value_on_init(self):
        form = self.S3UploadFormWithMockPolicy(storage=self.storage_mock)
        self.assertEqual(form.fields['policy'].initial, form.get_policy())

    def test_signature_is_set_as_field_initial_value_on_init(self):
        form = self.S3UploadFormWithMockPolicy(storage=self.storage_mock)
        self.assertEqual(form.fields['signature'].initial,
                         form.get_signature())

    def test_success_action_status_is_set_as_field_initial_value_on_init(self):
        form = self.S3UploadFormWithMockPolicy(storage=self.storage_mock)
        self.assertEqual(form.fields['success_action_status'].initial,
                         form.get_success_action_status_code())

    # add_prefix  # TODO

    # get_access_key

    def test_get_access_key_returns_storage_access_key(self):
        form = self.S3UploadFormWithMockPolicy(storage=self.storage_mock)
        self.assertEqual(form.get_access_key(), self.storage_mock.access_key)

    # get_acl

    def test_get_acl_returns_private(self):
        form = self.S3UploadFormWithMockPolicy(storage=self.storage_mock)
        self.assertEqual(form.get_acl(), 'private')

    # get_action  # TODO

    # get_cache_control

    def test_get_cache_control_returns_cache_control_header_from_storage(self):
        test_cache_control = 'TEST_CACHE_CONTROL'
        self.storage_mock.headers = {'Cache-Control': test_cache_control}
        form = self.S3UploadFormWithMockPolicy(storage=self.storage_mock)
        self.assertEqual(form.get_cache_control(), test_cache_control)

    def test_get_cache_control_returns_empty_string_if_not_set_on_storage(self):  # NOQA
        self.storage_mock.headers = {}
        form = self.S3UploadFormWithMockPolicy(storage=self.storage_mock)
        self.assertEqual(form.get_cache_control(), '')

    # get_conditions  # TODO

    # TODO - is this a good strategy?
    def test_get_conditions_calls_get_acl(self):
        form = self.S3UploadFormWithMockPolicy(storage=self.storage_mock)
        with mock.patch.object(form, 'get_acl',
                               mock.Mock(return_value='TEST_ACL')):
            form.get_conditions()
            self.assertTrue(form.get_acl.called)

    # get_expiration_time  # TODO

    def test_get_expiration_time_returns_expiration_time_if_already_set(self):
        test_expiration_time = 'EXPIRATION_TIME'
        form = self.S3UploadFormWithMockPolicy(storage=self.storage_mock)
        form._expiration_time = test_expiration_time
        self.assertEqual(form.get_expiration_time(), test_expiration_time)

    # get_key

    def test_get_key_calls_get_key_prefix(self):
        test_key_prefix = '/TEST_KEY_PREFIX/'
        form = self.S3UploadFormWithMockPolicy(storage=self.storage_mock)
        with mock.patch.object(form, 'get_key_prefix',
                               mock.Mock(return_value=test_key_prefix)):
            form.get_key()
            self.assertTrue(form.get_key_prefix.called)

    @mock.patch.object(forms.S3UploadForm, 'get_key_prefix',
                       mock.Mock(return_value='/TEST_KEY_PREFIX/'))
    def test_get_key_returns_string_which_ends_with_filename_placeholder(self):
        filename_placeholder = '${filename}'
        form = self.S3UploadFormWithMockPolicy(storage=self.storage_mock)
        self.assertTrue(form.get_key().endswith(filename_placeholder))

    def test_get_key_returns_string_which_starts_with_key_prefix(self):
        test_key_prefix = '/TEST_KEY_PREFIX/'
        form = self.S3UploadFormWithMockPolicy(storage=self.storage_mock)
        with mock.patch.object(form, 'get_key_prefix',
                               mock.Mock(return_value=test_key_prefix)):
            self.assertTrue(form.get_key().startswith(test_key_prefix))

    # get_policy  # TODO

    # get_signature  # TODO

    def test_get_signature_calls_get_secret_key(self):
        form = self.S3UploadFormWithMockPolicy(storage=self.storage_mock)
        with mock.patch.object(forms.S3UploadForm, 'get_secret_key',
                               mock.Mock(return_value='TEST_SECRET_KEY')):
            form.get_signature()
            self.assertTrue(form.get_secret_key.called)

    @mock.patch.object(forms.S3UploadForm, '__init__',
                       mock.Mock(return_value=None))
    @mock.patch.object(forms.S3UploadForm, 'get_policy',
                       mock.Mock(return_value='TEST_POLICY'))
    @mock.patch.object(forms.S3UploadForm, 'get_secret_key',
                       mock.Mock(return_value='TEST_SECRET_KEY'))
    def test_get_signature_calls_get_policy_key(self):
        form = forms.S3UploadForm()
        form.get_signature()
        self.assertTrue(form.get_policy.call_count == 1)

    # get_secret_key

    def test_get_secret_key_returns_storage_secret_key(self):
        form = self.S3UploadFormWithMockPolicy(storage=self.storage_mock)
        self.assertEqual(form.get_secret_key(), self.storage_mock.secret_key)

    # get_success_action_redirect

    def test_get_success_action_redirect_returns_set_success_action_redirect(self):  # NOQA
        test_success_action_redirect = 'TEST_SUCCESS_ACTION_REDIRECT'
        form = self.S3UploadFormWithMockPolicy(
            storage=self.storage_mock,
            success_action_redirect=test_success_action_redirect)
        self.assertEqual(form.get_success_action_redirect(),
                         test_success_action_redirect)

    # get_success_action_status_code

    def test_get_success_action_status_code_returns_set_success_action_status_code(self):  # NOQA
        test_success_action_status_code = 'TEST_SUCCESS_ACTION_STATUS_CODE'

        class TestSuccessActionStatusCodeForm(self.S3UploadFormWithMockPolicy):
            success_action_status_code = test_success_action_status_code

        form = TestSuccessActionStatusCodeForm(storage=self.storage_mock)
        self.assertEqual(form.get_success_action_status_code(),
                         test_success_action_status_code)
