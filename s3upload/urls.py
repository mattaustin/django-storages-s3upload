# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.conf.urls import patterns, include, url
from s3upload import views


urlpatterns = patterns('',

    url(r'^$', views.FormView.as_view(), name='upload'),

)
