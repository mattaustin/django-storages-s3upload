========================
django-storages-s3upload
========================


Direct (client-side) HTTP POST file upload to S3 using Django forms/views.


This project is under development, and so should be used in production
environments with a high degree of caution.

Docs: http://django-storages-s3upload.readthedocs.org/


Please be *VERY* careful with security considerations, and check you know
exactly what is happening. S3 HTTP POST upload will overwrite existing files if
the key matches. You will want to limit uploads to trusted users, and use
unique key prefixes. You will want to make sure that any processing of uploaded
files is safe.

See also:
https://docs.djangoproject.com/en/dev/topics/security/#user-uploaded-content


Features
--------

* Create signed forms for client-side uploading of files directly in to Amazon
  S3 buckets using HTTP POST:
  http://docs.aws.amazon.com/AmazonS3/latest/dev/HTTPPOSTForms.html

* A view to handle/validate the returned parameters from the upload, and a hook
  to process the uploaded file.

* An extended form/view which uses dropzone.js for handling multiple uploads
  with thumbnails and progress bars.


Requirements
------------

You'll need to set-up & configure an Amazon S3 Boto storage backend using
``django-storages``:
http://django-storages.readthedocs.org/en/latest/backends/amazon-S3.html


Installation
------------

Install django-storages-s3upload by running:


.. code-block:: sh

    pip install django-storages-s3upload


Contribute
----------

* Issue Tracker: https://github.com/mattaustin/django-storages-s3upload/issues
* Source Code: https://github.com/mattaustin/django-storages-s3upload


License
-------

The project is licensed under the Apache license 2.0.
