Change log
==========


0.1.5
-----

* Pass-through (the upload/redirect) and validate CSRF token when processing
  uploads.
* Prevent Dropzone 'success' styling until processing has also finished.
* A custom ``processed_key_generator`` can be passed to ValidateS3UploadForm
  instances.


0.1.4
-----

* ``ValidateS3UploadForm`` now renames/relocates files during the processing of
  uploads.
* Support for setting ``Cache-Control`` header.
* Ensure other http header data is retained when updating key metadata.


0.1.3
-----

* Ensure use of UTC when constructing expiration time for policy.
* Fixed bug when generating the form action url if the storage location was
  empty.


0.1.2
-----

* Fix for typo in settigs.
* Better file handling.


0.1.1
-----

* Added missing ``python-magic`` to setup.
* Fixed import typo in sphinx configuration.


0.1.0
-----

* Initial alpha/development release.
