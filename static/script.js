// State management
let selectedVideos = []; // Array of { type: 'file' | 'link', value: File | string }

setupDropZone('source-drop', 'source-input');
setupTargetUI();

function setupTargetUI() {
    const btnUpload = document.getElementById('btn-upload');
    const btnLink = document.getElementById('btn-link');
    const uploadSection = document.getElementById('upload-section');
    const linkSection = document.getElementById('link-section');
    const targetInput = document.getElementById('target-input');
    const addLinkBtn = document.getElementById('add-link-btn');
    const videoLinkInput = document.getElementById('video-link');

    btnUpload.addEventListener('click', () => {
        btnUpload.classList.add('active');
        btnLink.classList.remove('active');
        uploadSection.classList.remove('hidden');
        linkSection.classList.add('hidden');
    });

    btnLink.addEventListener('click', () => {
        btnLink.classList.add('active');
        btnUpload.classList.remove('active');
        linkSection.classList.remove('hidden');
        uploadSection.classList.add('hidden');
    });

    // File Input
    const dropZone = document.getElementById('target-drop');
    dropZone.addEventListener('click', () => targetInput.click());
    targetInput.addEventListener('change', () => {
        addVideos(Array.from(targetInput.files), 'file');
        targetInput.value = ""; // Reset for re-selection
    });

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        addVideos(Array.from(e.dataTransfer.files), 'file');
    });

    // Link Input
    addLinkBtn.addEventListener('click', () => {
        const url = videoLinkInput.value.trim();
        if (url) {
            if (url.startsWith('http')) {
                addVideos([url], 'link');
                videoLinkInput.value = "";
            } else {
                alert("Please enter a valid URL (starting with http/https)");
            }
        }
    });

    videoLinkInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') addLinkBtn.click();
    });
}

function addVideos(items, type) {
    items.forEach(item => {
        // Simple duplicate check
        const isDuplicate = selectedVideos.some(v => 
            type === 'file' ? (v.type === 'file' && v.value.name === item.name) : (v.type === 'link' && v.value === item)
        );
        
        if (!isDuplicate) {
            selectedVideos.push({ 
                type, 
                value: item, 
                status: 'Queued', 
                progress: 0,
                active: false
            });
        }
    });
    renderVideoList();
}

function removeVideo(index) {
    selectedVideos.splice(index, 1);
    renderVideoList();
}

function renderVideoList() {
    const list = document.getElementById('video-list');
    list.innerHTML = '';
    
    selectedVideos.forEach((video, index) => {
        const item = document.createElement('div');
        item.className = `video-item ${video.active ? 'active' : ''}`;
        
        const nameText = video.type === 'file' ? video.value.name : video.value;
        const typeLabel = video.type === 'file' ? '[File]' : '[Link]';
        
        const statusClass = video.status.toLowerCase();

        item.innerHTML = `
            <div class="video-item-header">
                <span class="name" title="${nameText}">${typeLabel} ${nameText}</span>
                <div style="display: flex; align-items: center;">
                    <span class="status-badge ${statusClass}">${video.status}</span>
                    <span class="remove" onclick="removeVideo(${index})">&times;</span>
                </div>
            </div>
            <div class="item-progress-container">
                <div class="item-progress-bar" style="width: ${video.progress}%"></div>
            </div>
        `;
        list.appendChild(item);
    });

    // Visual feedback for the drop zone
    const dropZone = document.getElementById('target-drop');
    if (selectedVideos.some(v => v.type === 'file')) {
        dropZone.style.borderColor = '#4ade80';
    } else {
        dropZone.style.borderColor = '';
    }
}

function setupDropZone(dropDetails, inputId) {
    const dropZone = document.getElementById(dropDetails);
    const input = document.getElementById(inputId);

    dropZone.addEventListener('click', () => input.click());
    input.addEventListener('change', () => {
        if (input.files && input.files.length > 0) {
            dropZone.querySelector('p').innerText = `${input.files[0].name}`;
            dropZone.style.borderColor = '#4ade80';
            dropZone.classList.add('selected');
        }
    });

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            input.files = e.dataTransfer.files;
            dropZone.querySelector('p').innerText = `${input.files[0].name}`;
            dropZone.style.borderColor = '#4ade80';
            dropZone.classList.add('selected');
        }
    });
}

// Ensure removeVideo is globally accessible for onclick handlers
window.removeVideo = removeVideo;

document.getElementById('swap-btn').addEventListener('click', async () => {
    const sourceInput = document.getElementById('source-input');

    if (sourceInput.files.length === 0 || selectedVideos.length === 0) {
        alert("Please select an input face and at least one target video!");
        return;
    }

    const formData = new FormData();
    formData.append('source_image', sourceInput.files[0]);

    // Send files and links separately
    const links = [];
    selectedVideos.forEach(v => {
        if (v.type === 'file') {
            formData.append('target_videos', v.value);
        } else {
            links.push(v.value);
        }
    });

    if (links.length > 0) {
        formData.append('video_links', JSON.stringify(links));
    }

    // UI Updates
    document.getElementById('swap-btn').classList.add('hidden');
    document.getElementById('status-panel').classList.remove('hidden');

    try {
        const response = await fetch('/swap', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || err.detail || "Server error");
        }

        const data = await response.json();
        const taskId = data.task_id;

        document.getElementById('status-text').innerText = "Queued for processing...";
        pollStatus(taskId);
    } catch (e) {
        alert("Error starting swap: " + e.message);
        document.getElementById('status-panel').classList.add('hidden');
        document.getElementById('swap-btn').classList.remove('hidden');
    }
});

async function pollStatus(taskId) {
    const statusText = document.getElementById('status-text');
    const interval = setInterval(async () => {
        try {
            const res = await fetch(`/status/${taskId}`);
            const data = await res.json();

            if (data.status === 'completed') {
                clearInterval(interval);
                // Mark all as completed
                selectedVideos.forEach(v => {
                    v.status = 'Completed';
                    v.progress = 100;
                    v.active = false;
                });
                renderVideoList();
                showResults(taskId, data.files);
            } else if (data.status === 'failed') {
                clearInterval(interval);
                alert("Processing failed: " + data.message);
                document.getElementById('status-panel').classList.add('hidden');
                document.getElementById('swap-btn').classList.remove('hidden');
            } else {
                if (data.message) {
                    statusText.innerText = data.message;
                    
                    /* 
                       Backend sends messages like:
                       "Downloading X linked videos..."
                       "Processing video 1/3: 25%"
                       "All videos processed"
                    */
                    const match = data.message.match(/Processing video (\d+)\/\d+: (\d+)%/);
                    if (match) {
                        const videoIdx = parseInt(match[1]) - 1;
                        const progress = parseInt(match[2]);
                        
                        // Update status of previous and current
                        selectedVideos.forEach((v, idx) => {
                            if (idx < videoIdx) {
                                v.status = 'Completed';
                                v.progress = 100;
                                v.active = false;
                            } else if (idx === videoIdx) {
                                v.status = 'Processing';
                                v.progress = progress;
                                v.active = true;
                            } else {
                                v.status = 'Queued';
                                v.progress = 0;
                                v.active = false;
                            }
                        });
                        renderVideoList();
                    }
                }
            }
        } catch (e) {
            console.error("Polling error", e);
        }
    }, 1000); // Poll faster for smoother progress
}

function showResults(taskId, files) {
    document.getElementById('status-panel').classList.add('hidden');
    const resultPanel = document.getElementById('result-panel');
    resultPanel.classList.remove('hidden');

    const list = document.getElementById('downloads-list');
    list.innerHTML = '';

    files.forEach(file => {
        const a = document.createElement('a');
        a.href = `/download/${taskId}/${file}`;
        a.innerText = `Download ${file}`;
        a.className = 'download-link';
        a.target = '_blank';
        list.appendChild(a);
    });
}
