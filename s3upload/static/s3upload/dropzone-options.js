function pingServer(file) {
    // Ping our server with the data returned by the S3 repsonse
    'use strict';

    // Although the file has been sucessfully uploads, don't show the success
    // styling until it has also been successfully processed.
    file.previewElement.classList.remove('dz-success');

    var s3Response = file.xhr.responseXML,
        request = new XMLHttpRequest(),
        formData = new FormData();

    request.open('POST', document.location.href, true);
    request.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
    request.setRequestHeader('X-CSRFToken', document.getElementById('s3upload').attributes['data-csrf-token'].value);

    request.onload = function () {
        if (this.status >= 200 && this.status < 400) {
            // Re-apply success styling
            file.previewElement.classList.add('dz-success');
        } else {
            // We reached our target server, but it returned an error.
            file.status = Dropzone.ERROR;
            Dropzone.forElement('#s3upload').emit('error', file, request.responseText);
        }
    };

    request.onerror = function () {
        // There was a connection error of some sort
        alert('Connection error');
    };

    formData.append('bucket', s3Response.getElementsByTagName('Bucket')[0].textContent);
    formData.append('key', s3Response.getElementsByTagName('Key')[0].textContent);
    formData.append('etag', s3Response.getElementsByTagName('ETag')[0].textContent);
    request.send(formData);
}


Dropzone.options.s3upload = {

    //maxFilesize: 10,

    //maxThumbnailFilesize: 10,

    parallelUploads: 5,

    init: function () {
        'use strict';
        this.on('success', function (file) {
            pingServer(file);
        });
    }

};
