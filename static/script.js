// WebSocket connection
let ws = null;
let typingMessageElement = null;
let isLoadingModel = false;

// DOM elements
const messagesContainer = document.getElementById('messages');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const statusIndicator = document.querySelector('.status-indicator');
const statusText = document.querySelector('.status-text');
const modelSelect = document.getElementById('modelSelect');

// Attach UX and per-chat RAG state
const attachButton = document.getElementById('attachButton');
const filePicker = document.getElementById('filePicker');
const activeSourceChip = document.getElementById('activeSourceChip');
const activeSourceText = document.getElementById('activeSourceText');
const clearSourceBtn = document.getElementById('clearSourceBtn');
let activeRagSource = null; // filename string when a doc is attached

// Load available models
async function loadAvailableModels() {
    try {
        const response = await fetch('/api/models');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        modelSelect.innerHTML = '';
        Object.entries(data.available_models).forEach(([modelId, modelInfo]) => {
            const option = document.createElement('option');
            option.value = modelId;
            option.textContent = `${modelInfo.name} (${modelInfo.size})`;
            option.title = modelInfo.description;
            if (modelId === data.current_model) option.selected = true;
            modelSelect.appendChild(option);
        });
        modelSelect.disabled = false;
    } catch (error) {
        console.error('Failed to load models:', error);
        modelSelect.innerHTML = '<option>Error loading models</option>';
        setTimeout(loadAvailableModels, 2000);
    }
}

// Handle model change
modelSelect.addEventListener('change', async (e) => {
    const selectedModel = e.target.value;
    if (isLoadingModel) return;
    isLoadingModel = true;
    modelSelect.disabled = true;
    sendButton.disabled = true;
    messageInput.disabled = true;
    const loadingMsg = addMessage(`🔄 Loading ${selectedModel}... Please wait, this may take a minute.`, 'loading');
    try {
        const response = await fetch('/api/models/load', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ model: selectedModel })
        });
        const result = await response.json();
        loadingMsg.remove();
        if (result.success) {
            addMessage(`✅ ${selectedModel} loaded successfully! You can start chatting now.`, 'system');
        } else {
            addMessage(`❌ Failed to load model: ${result.message}`, 'error');
        }
    } catch (error) {
        loadingMsg.remove();
        addMessage(`❌ Error loading model: ${error.message}`, 'error');
    } finally {
        isLoadingModel = false;
        modelSelect.disabled = false;
        sendButton.disabled = false;
        messageInput.disabled = false;
        messageInput.focus();
    }
});

// Initialize WebSocket connection
function connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    ws = new WebSocket(wsUrl);
    ws.onopen = () => {
        updateConnectionStatus('connected', 'Connected');
        sendButton.disabled = false;
    };
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleMessage(data);
    };
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        updateConnectionStatus('disconnected', 'Connection error');
    };
    ws.onclose = () => {
        updateConnectionStatus('disconnected', 'Disconnected');
        sendButton.disabled = true;
        setTimeout(() => {
            updateConnectionStatus('connecting', 'Reconnecting...');
            connect();
        }, 3000);
    };
}

// Update connection status
function updateConnectionStatus(status, text) {
    statusIndicator.className = `status-indicator ${status}`;
    statusText.textContent = text;
}

// Handle incoming messages
function handleMessage(data) {
    const { type, message } = data;
    if (type === 'typing') {
        showTypingIndicator(message);
    } else {
        removeTypingIndicator();
        addMessage(message, type);
    }
}

// Add message to chat
function addMessage(text, type) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.textContent = text;
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
    return messageDiv;
}

function showTypingIndicator(text) {
    if (!typingMessageElement) {
        typingMessageElement = document.createElement('div');
        typingMessageElement.className = 'message typing';
        messagesContainer.appendChild(typingMessageElement);
    }
    typingMessageElement.textContent = text;
    scrollToBottom();
}

function removeTypingIndicator() {
    if (typingMessageElement) {
        typingMessageElement.remove();
        typingMessageElement = null;
    }
}

function scrollToBottom() {
    messagesContainer.parentElement.scrollTop = messagesContainer.parentElement.scrollHeight;
}

function sendMessage() {
    const message = messageInput.value.trim();
    if (!message || !ws || ws.readyState !== WebSocket.OPEN) return;
    const payload = { message };
    if (activeRagSource) payload.sources = [activeRagSource];
    console.log('[DEBUG] Sending WebSocket payload:', JSON.stringify(payload));
    console.log('[DEBUG] activeRagSource:', activeRagSource);
    ws.send(JSON.stringify(payload));
    messageInput.value = '';
    messageInput.focus();
}

// Event listeners
sendButton.addEventListener('click', sendMessage);
messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});

// Initialize when page loads (handle scripts at end of body)
function initApp() {
    console.debug('[INIT] Starting app init');
    loadAvailableModels();
    connect();
    initAttachUI();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}

// ------- Attach UX and per-chat RAG integration -------
function initAttachUI() {
    console.log('[RAG] initAttachUI called');
    console.log('[RAG] attachButton:', attachButton);
    console.log('[RAG] filePicker:', filePicker);
    console.log('[RAG] clearSourceBtn:', clearSourceBtn);
    
    if (attachButton) {
        attachButton.addEventListener('click', () => {
            console.log('[RAG] attachButton clicked - triggering file picker');
            if (filePicker) {
                filePicker.click();
            } else {
                addMessage('❌ File picker not available', 'error');
            }
        });
        console.log('[RAG] attachButton click listener added');
    } else {
        console.error('[RAG] attachButton element not found!');
    }
    
    if (clearSourceBtn) {
        clearSourceBtn.addEventListener('click', clearActiveSource);
        console.log('[RAG] clearSourceBtn listener added');
    }
    
    if (filePicker) {
        filePicker.addEventListener('change', onAttachFile);
        console.log('[RAG] filePicker change listener added to call onAttachFile');
    } else {
        console.error('[RAG] filePicker element not found!');
    }
}

async function onAttachFile(e) {
    console.log('[RAG] onAttachFile triggered!', e);
    const files = e.target.files;
    console.log('[RAG] files selected:', files);
    if (!files || files.length === 0) {
        console.log('[RAG] No files selected');
        return;
    }
    const file = files[0];
    try {
        addMessage(`🔄 Uploading and indexing ${file.name} ...`, 'loading');
        console.log('[DEBUG] Starting upload:', { name: file.name, size: file.size, type: file.type });
        const fd = new FormData();
        fd.append('file', file);
        const resp = await fetch('/api/rag/ingest_file', { method: 'POST', body: fd });
        console.log('[DEBUG] Upload response status:', resp.status);
        const result = await resp.json();
        console.log('[DEBUG] Upload result:', result);
        const loadingEls = document.querySelectorAll('.message.loading');
        if (loadingEls.length) loadingEls[loadingEls.length - 1].remove();
        if (result.success) {
            activeRagSource = result.source;
            showActiveSource(result.source);
            addMessage(`✅ Attached ${result.source} for this chat. Your next messages will use it.`, 'system');
        } else {
            addMessage(`❌ Upload failed: ${result.message || 'Unknown error'}`, 'error');
            console.error('[ERROR] Upload failed:', result);
        }
    } catch (err) {
        addMessage(`❌ Upload error: ${err.message}`, 'error');
    } finally {
        if (filePicker) filePicker.value = '';
    }
}

function showActiveSource(name) {
    if (!activeSourceChip || !activeSourceText) return;
    activeSourceText.textContent = name;
    activeSourceChip.style.display = 'inline-flex';
}

function clearActiveSource() {
    activeRagSource = null;
    if (activeSourceChip) activeSourceChip.style.display = 'none';
}
