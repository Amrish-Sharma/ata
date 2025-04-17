document.addEventListener('DOMContentLoaded', () => {
    const uploadForm = document.getElementById('uploadForm');
    
    const uploadProgress = document.getElementById('uploadProgress');
    const uploadProgressBar = document.getElementById('uploadProgressBar');
    const uploadProgressText = document.getElementById('uploadProgressText');
    const transcribeProgress = document.getElementById('transcribeProgress');
    const transcribeProgressBar = document.getElementById('transcribeProgressBar');
    const transcribeProgressText = document.getElementById('transcribeProgressText');
    const resultDiv = document.getElementById('result');


    uploadForm.onsubmit = async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        
        // Show progress bars
        uploadProgress.classList.remove('hidden');
        transcribeProgress.classList.remove('hidden');
        
        try {
            const xhr = new XMLHttpRequest();
            
            // Track upload progress
            xhr.upload.onprogress = (event) => {
                if (event.lengthComputable) {
                    const percentComplete = Math.round((event.loaded / event.total) * 100);
                    uploadProgressBar.style.width = percentComplete + '%';
                    uploadProgressText.textContent = percentComplete + '%';
                }
            };

            // Create a promise to handle the XHR response
            const response = await new Promise((resolve, reject) => {
                xhr.onload = () => resolve(xhr.response);
                xhr.onerror = () => reject(xhr.statusText);
                xhr.open('POST', '/upload');
                xhr.send(formData);
            });

            // Start polling for transcription progress
            const pollProgress = async () => {
                const progressResponse = await fetch('/transcribe-progress');
                const progress = await progressResponse.json();
                
                transcribeProgressBar.style.width = progress.percentage + '%';
                transcribeProgressText.textContent = 
                    `${progress.percentage}% - ${progress.status}`;

                if (progress.percentage < 100) {
                    setTimeout(pollProgress, 1000);
                }
            };

            pollProgress();
            
            resultDiv.innerHTML = response;
        } catch (error) {
            console.error('Error:', error);
            resultDiv.innerHTML = `<p class="error">Error: ${error.message}</p>`;
        }
    };
});