document.getElementById('uploadForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const fileInput = document.getElementById('fileInput');
    const feedback = document.getElementById('feedback');
    if (!fileInput.files.length) {
        feedback.textContent = 'Please select an image.';
        return;
    }
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    feedback.textContent = 'Uploading...';
    try {
        const res = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        if (data.success) {
            feedback.textContent = 'Upload successful!';
        } else {
            feedback.textContent = 'Upload failed: ' + (data.error || 'Unknown error');
        }
    } catch (err) {
        feedback.textContent = 'Error: ' + err.message;
    }
});
