document.getElementById('uploadForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const fileInput = document.getElementById('fileInput');
    const feedback = document.getElementById('feedback');
    
    if (!fileInput.files.length) {
        feedback.textContent = 'Please select one or more images.';
        return;
    }

    const files = Array.from(fileInput.files);
    const totalFiles = files.length;
    
    feedback.innerHTML = `
        <div>Uploading ${totalFiles} file${totalFiles > 1 ? 's' : ''}...</div>
        <div id="progress">
            <div id="progressBar" style="width: 0%; height: 20px; background: #667eea; border-radius: 10px; transition: width 0.3s;"></div>
            <div id="progressText">0 / ${totalFiles}</div>
        </div>
        <div id="uploadResults"></div>
    `;

    let completed = 0;
    let successful = 0;
    let failed = 0;
    const results = [];

    // Upload files sequentially to avoid overwhelming the server
    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const formData = new FormData();
        formData.append('file', file);

        try {
            const res = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();
            
            completed++;
            if (data.success) {
                successful++;
                results.push(`✅ ${file.name}: Success`);
            } else {
                failed++;
                results.push(`❌ ${file.name}: ${data.error || 'Unknown error'}`);
            }
        } catch (err) {
            completed++;
            failed++;
            results.push(`❌ ${file.name}: ${err.message}`);
        }

        // Update progress
        const progress = (completed / totalFiles) * 100;
        document.getElementById('progressBar').style.width = `${progress}%`;
        document.getElementById('progressText').textContent = `${completed} / ${totalFiles}`;
        
        // Update results
        document.getElementById('uploadResults').innerHTML = results.map(result => 
            `<div style="margin: 2px 0; font-size: 0.9rem;">${result}</div>`
        ).join('');
    }

    // Final summary
    const summaryColor = failed === 0 ? '#4caf50' : (successful === 0 ? '#f44336' : '#ff9800');
    feedback.innerHTML += `
        <div style="margin-top: 15px; padding: 10px; background: ${summaryColor}; color: white; border-radius: 5px; font-weight: bold;">
            Summary: ${successful} successful, ${failed} failed out of ${totalFiles} total
        </div>
    `;

    // Reset form if all uploads were successful
    if (failed === 0) {
        setTimeout(() => {
            fileInput.value = '';
            feedback.innerHTML = `<div style="color: #4caf50; font-weight: bold;">All uploads completed successfully! 🎉</div>`;
        }, 2000);
    }
});
