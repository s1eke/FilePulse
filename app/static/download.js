// Download functionality with progress tracking
const shareCodeInput = document.getElementById('shareCodeInput');
const fetchBtn = document.getElementById('fetchBtn');
const fileInfoSection = document.getElementById('fileInfoSection');
const downloadBtn = document.getElementById('downloadBtn');
const progressContainer = document.getElementById('progressContainer');
const errorMessage = document.getElementById('errorMessage');

let currentShareCode = null;
let fileInfo = null;
let downloadStartTime = null;

// Check URL for share code parameter
const urlParams = new URLSearchParams(window.location.search);
const urlShareCode = urlParams.get('code');
if (urlShareCode) {
    shareCodeInput.value = urlShareCode;
    fetchFileInfo();
}

fetchBtn.addEventListener('click', fetchFileInfo);

shareCodeInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        fetchFileInfo();
    }
});

async function fetchFileInfo() {
    const shareCode = shareCodeInput.value.trim();

    if (!shareCode) {
        showError('Please enter a share code');
        return;
    }

    hideError();
    fetchBtn.disabled = true;
    fetchBtn.textContent = 'Loading...';

    try {
        const response = await fetch(`/api/file/${shareCode}`);

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'File not found');
        }

        fileInfo = await response.json();
        currentShareCode = shareCode;
        displayFileInfo(fileInfo);

    } catch (error) {
        showError(error.message);
        fileInfoSection.classList.remove('active');
    } finally {
        fetchBtn.disabled = false;
        fetchBtn.textContent = 'Get File Info';
    }
}

function displayFileInfo(info) {
    fileInfoSection.classList.add('active');

    document.getElementById('fileName').textContent = truncateFileName(info.filename, 20);
    document.getElementById('fileSize').textContent = formatFileSize(info.file_size);

    const expiryDate = new Date(info.expiry_time);
    document.getElementById('expiryDate').textContent = expiryDate.toLocaleDateString();
}

downloadBtn.addEventListener('click', downloadFile);

async function downloadFile() {
    if (!currentShareCode || !fileInfo) return;

    hideError();
    downloadBtn.disabled = true;
    downloadBtn.textContent = 'Preparing download...';
    progressContainer.classList.add('active');

    downloadStartTime = Date.now();

    try {
        const response = await fetch(`/api/download/${currentShareCode}`);

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Download failed');
        }

        // Get content length
        const contentLength = parseInt(response.headers.get('Content-Length') || fileInfo.file_size);

        // Read stream with progress tracking
        const reader = response.body.getReader();
        const chunks = [];
        let receivedBytes = 0;

        while (true) {
            const { done, value } = await reader.read();

            if (done) break;

            chunks.push(value);
            receivedBytes += value.length;

            updateProgress(receivedBytes, contentLength);
        }

        // Combine chunks into blob
        const blob = new Blob(chunks);

        // Create download link
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = fileInfo.filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        // Show success
        downloadBtn.textContent = '✓ Download Complete';
        setTimeout(() => {
            downloadBtn.textContent = '⬇️ Download File';
            downloadBtn.disabled = false;
            progressContainer.classList.remove('active');
            resetProgress();
        }, 3000);

    } catch (error) {
        showError('Download failed: ' + error.message);
        downloadBtn.disabled = false;
        downloadBtn.textContent = '⬇️ Download File';
        progressContainer.classList.remove('active');
        resetProgress();
    }
}

function updateProgress(loaded, total) {
    const percent = (loaded / total) * 100;

    document.getElementById('progressBar').style.width = percent + '%';
    document.getElementById('progressPercent').textContent = Math.round(percent) + '%';

    // Calculate speed
    const elapsed = (Date.now() - downloadStartTime) / 1000; // seconds
    const speed = loaded / elapsed; // bytes per second
    document.getElementById('downloadSpeed').textContent = formatSpeed(speed);

    // Calculate time remaining
    const remaining = (total - loaded) / speed; // seconds
    document.getElementById('timeRemaining').textContent = formatTime(remaining);
}

function resetProgress() {
    document.getElementById('progressBar').style.width = '0%';
    document.getElementById('progressPercent').textContent = '0%';
    document.getElementById('downloadSpeed').textContent = '0 MB/s';
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
