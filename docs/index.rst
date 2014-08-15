django-storages-s3upload
========================

django-storages-s3upload provides forms and views for direct HTTP post to S3.
It is an addition for the Amazon S3 boto storage backend provided by
django-storages.

Please be *VERY* careful with security considerations, and check you know
exactly what is happening. S3 HTTP POST upload will overwrite existing files if
the key matches. You will want to limit uploads to trusted users, and use
unique key prefixes. You will want to make sure that any processing of uploaded
files is safe.

See also:
https://docs.djangoproject.com/en/dev/topics/security/#user-uploaded-content


The goals of this Django app are to:

* Create signed forms for posting files directly in to Amazon S3 buckets.
* Provide views so that it is possible to process files which have been
  successfully uploaded.
* Provide an extended form class which uses dropzone.js for handling multiple
  uploads with thumbnails and progress bars.


Quick Start
-----------

If you already have an Amazon S3 Boto backend configured as your project's
``DEFAULT_FILE_STORAGE``, then it's easy to get an example going by extending
``S3UploadFormView`` or ``DropzoneS3UploadFormView``:


.. code-block:: python

    class MyFormView(DropzoneS3UploadFormView):

        upload_to = 'test-uploads/'


Contents
--------

.. toctree::
   :maxdepth: 2

   changes
   api/index
