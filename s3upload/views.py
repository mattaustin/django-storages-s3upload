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
from .forms import DropzoneS3UploadForm, S3UploadForm, ValidateS3UploadForm
from django.core.files.storage import default_storage
from django.core.urlresolvers import get_callable
from django.http import HttpResponse, HttpResponseBadRequest
from django.middleware.csrf import REASON_BAD_TOKEN, REASON_NO_CSRF_COOKIE
from django.utils.crypto import constant_time_compare
from django.utils.decorators import method_decorator
from django.views import generic
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie

try:
    from urllib import parse as urlparse
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode
    import urlparse


class S3UploadFormView(generic.edit.FormMixin,
                       generic.base.TemplateResponseMixin, generic.View):

    content_type_prefix = ''  # e.g. 'image/', 'text/'

    form_class = S3UploadForm

    process_to = None  # e.g. 'foo/bar/'

    processed_key_generator = None

    set_content_type = settings.SET_CONTENT_TYPE

    storage = default_storage

    template_name = 's3upload/form.html'

    upload_to = None  # e.g. 'foo/bar/'

    def form_invalid(self, form):
        return HttpResponseBadRequest('Upload does not validate.')

    def form_valid(self, form, *args, **kwargs):
        form.process_upload(set_content_type=self.set_content_type)
        if self.request.is_ajax():
            return HttpResponse()
        else:
            return super(S3UploadFormView, self).form_valid(form, *args,
                                                            **kwargs)

    @method_decorator(ensure_csrf_cookie)
    def get(self, request, *args, **kwargs):

        # If 'key' is in GET params, we're dealing with a new upload
        # (S3 redirect) - we should treat this like a POST and validate csrf.
        if 'key' in request.GET:

            csrf_token = request.META.get('CSRF_COOKIE', None)
            request_csrf_token = request.GET.get('csrfmiddlewaretoken', '')
            failure_view = get_callable(settings.CSRF_FAILURE_VIEW)

            if not csrf_token:
                return failure_view(request, REASON_NO_CSRF_COOKIE)
            if not constant_time_compare(request_csrf_token, csrf_token):
                return failure_view(request, REASON_BAD_TOKEN)

            return self.validate_upload()

        form_class = self.get_form_class()
        form = self.get_form(form_class)
        return self.render_to_response(self.get_context_data(form=form))

    def get_content_type_prefix(self):
        return self.content_type_prefix

    def get_upload_to(self):
        return self.upload_to

    def get_form_kwargs(self, *args, **kwargs):
        form_kwargs = super(S3UploadFormView, self).get_form_kwargs(*args,
                                                                    **kwargs)
        form_kwargs.update(
            {'storage': self.get_storage(),
             'upload_to': self.get_upload_to(),
             'content_type_prefix': self.get_content_type_prefix(),
             'success_action_redirect': self.get_success_action_redirect()})
        return form_kwargs

    def get_process_to(self):
        return self.process_to

    def get_processed_key_generator(self):
        return self.processed_key_generator

    def get_storage(self):
        return self.storage

    def get_success_action_redirect(self):
        base_uri = self.request.build_absolute_uri()
        parts = list(urlparse.urlsplit(base_uri))

        csrf_token = self.request.META.get('CSRF_COOKIE', None)
        if csrf_token:
            query = urlparse.parse_qs(parts[3])  # Parse querystring
            query.update({'csrfmiddlewaretoken': csrf_token})  # Add csrf token
            parts[3] = urlencode(query)  # Replace querystring

        return urlparse.urlunsplit(parts)

    @method_decorator(csrf_protect)
    def post(self, *args, **kwargs):
        return self.validate_upload()

    def validate_upload(self):
        # Validate a new upload
        data = {'bucket_name': self.request.REQUEST.get('bucket'),
                'key_name': self.request.REQUEST.get('key'),
                'etag': self.request.REQUEST.get('etag')}
        form = ValidateS3UploadForm(
            data=data, storage=self.get_storage(),
            content_type_prefix=self.get_content_type_prefix(),
            upload_to=self.get_upload_to(), process_to=self.get_process_to(),
            processed_key_generator=self.get_processed_key_generator())
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class DropzoneS3UploadFormView(S3UploadFormView):

    form_class = DropzoneS3UploadForm

    template_name = 's3upload/dropzone_form.html'

    def get_success_action_redirect(self):
        return None
