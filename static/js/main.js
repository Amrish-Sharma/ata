document.addEventListener('DOMContentLoaded', () => {
    const uploadForm = document.getElementById('uploadForm');
    const fileInput = document.getElementById('fileInput');
    const dropzone = document.getElementById('dropzone');
    const urlInput = document.getElementById('urlInput');
    const resultDiv = document.getElementById('result');

    // Dropzone functionality
    dropzone.addEventListener("click", () => fileInput.click());
    dropzone.addEventListener("dragover", e => {
        e.preventDefault();
        dropzone.classList.add("dragover");
    });
    dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));
    dropzone.addEventListener("drop", e => {
        e.preventDefault();
        dropzone.classList.remove("dragover");
        fileInput.files = e.dataTransfer.files;
    });

    // Unified handler for both file and URL submission
    uploadForm.onsubmit = async (e) => {
        e.preventDefault();

        const file = fileInput.files[0];
        const youtubeURL = urlInput.value.trim();

        // Clear any previous result (but not the form)
        resultDiv.innerHTML = '';

        try {
            if (file) {
                // If file is selected, send to server
                const formData = new FormData();
                formData.append("file", file);

                const response = await fetch("/upload", {
                    method: "POST",
                    body: formData
                });

                const resultHTML = await response.text();
                resultDiv.innerHTML = resultHTML; // Only show the result in the result section
            } else if (youtubeURL) {
                // If YouTube URL is provided, send to server
                const formData = new URLSearchParams();
                formData.append("youtube_url", youtubeURL);

                const response = await fetch("/transcribe-url", {
                    method: "POST",
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded'
                    },
                    body: formData
                });

                const resultHTML = await response.text();
                resultDiv.innerHTML = resultHTML; // Only show the result in the result section
            } else {
                alert("Please upload a file or enter a YouTube URL.");
            }
        } catch (error) {
            console.error("Error:", error);
            resultDiv.innerHTML = `<p class="error">Error: ${error.message}</p>`;
        }
    };
});
