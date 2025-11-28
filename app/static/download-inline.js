// Download functionality for inline mode on homepage
let currentShareCode = null;
let fileInfo = null;
let downloadStartTime = null;

const shareCodeInput = document.getElementById('shareCodeInput');
const fetchBtn = document.getElementById('fetchBtn');
const fileInfoSection = document.getElementById('fileInfoSection');
const downloadBtn = document.getElementById('downloadBtn');
const downloadProgressContainer = document.getElementById('downloadProgressContainer');

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

    document.getElementById('downloadFileName').textContent = truncateFileName(info.filename, 20);
    document.getElementById('downloadFileSize').textContent = formatFileSize(info.file_size);

    const expiryDate = new Date(info.expiry_time);
    document.getElementById('downloadExpiryDate').textContent = expiryDate.toLocaleDateString();
}

downloadBtn.addEventListener('click', downloadFile);

async function downloadFile() {
    if (!currentShareCode || !fileInfo) return;

    hideError();
    downloadBtn.disabled = true;
    downloadBtn.textContent = 'Preparing download...';
    downloadProgressContainer.classList.add('active');

    downloadStartTime = Date.now();

    try {
        const response = await fetch(`/api/download/${currentShareCode}`);

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Download failed');
        }

        const contentLength = parseInt(response.headers.get('Content-Length') || fileInfo.file_size);
        const reader = response.body.getReader();
        const chunks = [];
        let receivedBytes = 0;

        while (true) {
            const { done, value } = await reader.read();

            if (done) break;

            chunks.push(value);
            receivedBytes += value.length;

            updateDownloadProgress(receivedBytes, contentLength);
        }

        const blob = new Blob(chunks);
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = fileInfo.filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        downloadBtn.textContent = '✓ Download Complete';
        setTimeout(() => {
            downloadBtn.textContent = '⬇️ Download File';
            downloadBtn.disabled = false;
            downloadProgressContainer.classList.remove('active');
            resetDownloadProgress();
        }, 3000);

    } catch (error) {
        showError('Download failed: ' + error.message);
        downloadBtn.disabled = false;
        downloadBtn.textContent = '⬇️ Download File';
        downloadProgressContainer.classList.remove('active');
        resetDownloadProgress();
    }
}

function updateDownloadProgress(loaded, total) {
    const percent = (loaded / total) * 100;

    document.getElementById('downloadProgressBar').style.width = percent + '%';
    document.getElementById('downloadProgressPercent').textContent = Math.round(percent) + '%';

    const elapsed = (Date.now() - downloadStartTime) / 1000;
    const speed = loaded / elapsed;
    document.getElementById('downloadSpeed').textContent = formatSpeed(speed);

    const remaining = (total - loaded) / speed;
    document.getElementById('downloadTimeRemaining').textContent = formatTime(remaining);
}

function resetDownloadProgress() {
    document.getElementById('downloadProgressBar').style.width = '0%';
    document.getElementById('downloadProgressPercent').textContent = '0%';
    document.getElementById('downloadSpeed').textContent = '0 MB/s';
    document.getElementById('downloadTimeRemaining').textContent = '--:--';
}
