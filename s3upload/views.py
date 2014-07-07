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
from django.core.files.storage import default_storage
from django.http import HttpResponseBadRequest
from django.views import generic
from .forms import S3UploadForm, ValidateS3UploadForm


class S3UploadFormView(generic.edit.FormMixin,
                       generic.base.TemplateResponseMixin, generic.View):

    # TODO: Split new upload from upload validation?
    # TODO: Set additional metadata for upload, e.g. cache?

    content_type_prefix = ''  # e.g. 'image/', 'text/'

    form_class = S3UploadForm

    storage = default_storage

    template_name = 'filetest/form.html'

    upload_to = ''  # e.g. 'foo/bar/'

    def form_invalid(self, form):
        return HttpResponseBadRequest('Upload does not validate.')

    def form_valid(self, form, *args, **kwargs):
        form.set_content_type()
        return super(S3UploadFormView, self).form_valid(form, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        # If 'key' is in GET params, we're dealing with a new upload
        if 'key' in request.GET:
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
            {'storage': self.get_storage(), 'upload_to': self.get_upload_to(),
             'content_type_prefix': self.get_content_type_prefix(),
             'success_action_redirect': self.get_success_action_redirect()})
        return form_kwargs

    def get_storage(self):
        return self.storage

    def get_success_action_redirect(self):
        return self.request.build_absolute_uri()

    def validate_upload(self):
        # Validate a new upload
        data = {'bucket_name': self.request.GET.get('bucket'),
                'key_name': self.request.GET.get('key'),
                'etag': self.request.GET.get('etag')}
        form = ValidateS3UploadForm(
            data=data, storage=self.get_storage(),
            content_type_prefix=self.get_content_type_prefix(),
            upload_to=self.get_upload_to())
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
