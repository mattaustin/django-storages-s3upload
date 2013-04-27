# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.views import generic
from s3upload.forms import S3UploadForm


class FormView(generic.FormView):

    form_class = S3UploadForm
    template_name = 's3upload/form.html'
