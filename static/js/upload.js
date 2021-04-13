document.getElementById('upload').style.opacity = '20%';

var activated = false;

function update() {
  if (activated) {
    document.getElementById('upload').innerHTML = '';
    document.getElementById('upload').innerHTML = `
      <div class="upload-button" id="upload-button">
        Select or drop file
      </div>
      <small class="subtitle" style="margin-left: 5px;">2GB size limit</small>
    `;
    activated = false;
  }

  if (
    document.getElementById('user').value &&
    document.getElementById('title').value
  ) {
    activated = true;
    document.getElementById('upload').style.opacity = '100%';
    var r = new Resumable({
      target: '/api/upload',
      chunkSize: 10 * 1024 * 1024,
      maxFiles: 1,
      simultaneousUploads: 10,
      testChunks: false,
      query:{
        service: document.getElementById('service').value,
        user: document.getElementById('user').value,
        title: document.getElementById('title').value,
        content: document.getElementById('content').value
      }
    });

    r.on('fileAdded', function () {
      document.getElementById('upload-button').style.backgroundColor = '#ffc107';
      document.getElementById('upload-button').style.color = '#000';
      document.getElementById('upload-button').innerHTML = 'Uploading...';
      r.upload();
    });

    r.on('fileSuccess', function() {
      document.getElementById('upload-button').style.backgroundColor = '#77dd77';
      document.getElementById('upload-button').style.color = '#000';
      document.getElementById('upload-button').innerHTML = 'Done!';
      document.getElementById('upload-button').replaceWith(document.getElementById('upload-button').cloneNode(true))
    });

    r.on('fileError', function(file, msg) {
      document.getElementById('upload-button').style.backgroundColor = '#ff6961';
      document.getElementById('upload-button').style.color = '#000';
      document.getElementById('upload-button').innerHTML = msg;
    });

    r.on('fileProgress', function(file) {
      document.getElementById('upload-button').innerHTML = `Uploading... (${Math.floor((file.progress() / 1) * 100)}%)`;
    });
    
    r.assignBrowse(document.getElementById('upload-button'));
    r.assignDrop(document.getElementById('upload-button'));
  } else {
    document.getElementById('upload').style.opacity = '20%';
  }
}

document.getElementById('user').addEventListener('input', update)
document.getElementById('title').addEventListener('input', update)
document.getElementById('content').addEventListener('input', update)