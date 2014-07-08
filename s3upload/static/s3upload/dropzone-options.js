Dropzone.options.s3upload = {

  //maxFilesize: 10,

  //maxThumbnailFilesize: 10,

  parallelUploads: 5,

  init: function() {
    this.on('success', function(file) {
        pingServer(file);
    });
  }

};


function pingServer(file) {
  // Ping our server with the data returned by the S3 repsonse

  var s3Response = file.xhr.responseXML;
  var request = new XMLHttpRequest();
  request.open('POST', document.location.href, true);
  request.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
  request.setRequestHeader('X-CSRFToken', document.getElementById('s3upload').attributes['data-csrf-token'].value);

  request.onload = function() {
    if (this.status >= 200 && this.status < 400) {
      // Success!
    } else {
      // We reached our target server, but it returned an error
      alert('Server error');
    }
  };

  request.onerror = function() {
    // There was a connection error of some sort
    alert('Connection error');
  };

  var formData = new FormData();
  formData.append('bucket', s3Response.getElementsByTagName('Bucket')[0].textContent)
  formData.append('key', s3Response.getElementsByTagName('Key')[0].textContent)
  formData.append('etag', s3Response.getElementsByTagName('ETag')[0].textContent)
  request.send(formData);

}
