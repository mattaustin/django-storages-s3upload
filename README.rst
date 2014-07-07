========================
django-storages-s3upload
========================

This project is under development, as in its current state is far from
finished.


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
