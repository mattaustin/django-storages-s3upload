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
from datetime import timedelta
from django.conf import settings


EXPIRATION_TIMEDELTA = getattr(
    settings, 'S3UPLOAD_EXPIRATION_TIMEDELTA', timedelta(minutes=30))


SET_CONTENT_TYPE = getattr(settings, 'S3UPLOAD_SET_CONTENT_TYPE', True)
