// Upload functionality with progress tracking
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const uploadBtn = document.getElementById('uploadBtn');
const progressContainer = document.getElementById('progressContainer');
const resultContainer = document.getElementById('resultContainer');
const errorMessage = document.getElementById('errorMessage');
const copyBtn = document.getElementById('copyBtn');
const newUploadBtn = document.getElementById('newUploadBtn');

let selectedFile = null;
let uploadStartTime = null;

// File selection handlers
uploadArea.addEventListener('click', () => fileInput.click());

uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('drag-over');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('drag-over');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('drag-over');

    if (e.dataTransfer.files.length > 0) {
        handleFileSelect(e.dataTransfer.files[0]);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileSelect(e.target.files[0]);
    }
});

function handleFileSelect(file) {
    const maxSize = 100 * 1024 * 1024; // 100MB

    if (file.size > maxSize) {
        showError('File size exceeds 100MB limit');
        return;
    }

    selectedFile = file;
    uploadArea.querySelector('.upload-text').textContent = `Selected: ${file.name}`;
    uploadArea.querySelector('.upload-hint').textContent = `${formatFileSize(file.size)} - Ready to upload`;
    uploadBtn.style.display = 'block';
}

uploadBtn.addEventListener('click', uploadFile);

async function uploadFile() {
    if (!selectedFile) return;

    hideError();
    uploadBtn.disabled = true;
    progressContainer.classList.add('active');
    resultContainer.classList.remove('active');

    const formData = new FormData();
    formData.append('file', selectedFile);

    uploadStartTime = Date.now();
    let uploadedBytes = 0;

    try {
        // Create XMLHttpRequest for progress tracking
        const xhr = new XMLHttpRequest();

        // Track upload progress
        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percentComplete = (e.loaded / e.total) * 100;
                updateProgress(percentComplete, e.loaded, e.total);
            }
        });

        // Handle completion
        xhr.addEventListener('load', () => {
            if (xhr.status === 200) {
                const response = JSON.parse(xhr.responseText);
                displayResult(response);
                progressContainer.classList.remove('active');
            } else {
                const error = JSON.parse(xhr.responseText);
                showError(error.detail || 'Upload failed');
                resetUpload();
            }
        });

        // Handle error
        xhr.addEventListener('error', () => {
            showError('Network error occurred');
            resetUpload();
        });

        // Send request
        xhr.open('POST', '/api/upload');
        xhr.send(formData);

    } catch (error) {
        showError('Upload failed: ' + error.message);
        resetUpload();
    }
}

function updateProgress(percent, loaded, total) {
    document.getElementById('progressBar').style.width = percent + '%';
    document.getElementById('progressPercent').textContent = Math.round(percent) + '%';

    // Calculate speed
    const elapsed = (Date.now() - uploadStartTime) / 1000; // seconds
    const speed = loaded / elapsed; // bytes per second
    document.getElementById('uploadSpeed').textContent = formatSpeed(speed);

    // Calculate time remaining
    const remaining = (total - loaded) / speed; // seconds
    document.getElementById('timeRemaining').textContent = formatTime(remaining);
}

function displayResult(data) {
    resultContainer.classList.add('active');

    document.getElementById('shareCode').textContent = data.share_code;
    document.getElementById('fileName').textContent = truncateFileName(data.filename, 20);
    document.getElementById('fileSize').textContent = formatFileSize(data.file_size);

    const expiryDate = new Date(data.expiry_time);
    document.getElementById('expiryDate').textContent = expiryDate.toLocaleDateString();

    // Store share code for copy functionality
    copyBtn.setAttribute('data-share-code', data.share_code);
}

copyBtn.addEventListener('click', () => {
    const shareCode = copyBtn.getAttribute('data-share-code');
    const shareUrl = `${window.location.origin}/download.html?code=${shareCode}`;

    navigator.clipboard.writeText(shareUrl).then(() => {
        const originalText = copyBtn.textContent;
        copyBtn.textContent = '✓ Copied!';
        setTimeout(() => {
            copyBtn.textContent = originalText;
        }, 2000);
    });
});

newUploadBtn.addEventListener('click', () => {
    resetUpload();
    resultContainer.classList.remove('active');
    uploadArea.querySelector('.upload-text').textContent = 'Drop your file here or click to browse';
    uploadArea.querySelector('.upload-hint').textContent = 'Maximum file size: 100MB';
    selectedFile = null;
    fileInput.value = '';
});

function resetUpload() {
    uploadBtn.disabled = false;
    progressContainer.classList.remove('active');
    document.getElementById('progressBar').style.width = '0%';
    document.getElementById('progressPercent').textContent = '0%';
    document.getElementById('uploadSpeed').textContent = '0 MB/s';
    document.getElementById('timeRemaining').textContent = '--:--';
}

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.add('active');
}

function hideError() {
    errorMessage.classList.remove('active');
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function formatSpeed(bytesPerSecond) {
    return formatFileSize(bytesPerSecond) + '/s';
}

function formatTime(seconds) {
    if (!isFinite(seconds) || seconds < 0) return '--:--';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function truncateFileName(filename, maxLength) {
    if (filename.length <= maxLength) return filename;
    const ext = filename.split('.').pop();
    const nameWithoutExt = filename.substring(0, filename.length - ext.length - 1);
    const truncated = nameWithoutExt.substring(0, maxLength - ext.length - 4);
    return `${truncated}...${ext}`;
}
