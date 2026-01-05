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

// Load available models
async function loadAvailableModels() {
    try {
        const response = await fetch('/api/models');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Clear existing options
        modelSelect.innerHTML = '';
        
        // Add model options
        Object.entries(data.available_models).forEach(([modelId, modelInfo]) => {
            const option = document.createElement('option');
            option.value = modelId;
            option.textContent = `${modelInfo.name} (${modelInfo.size})`;
            option.title = modelInfo.description;
            
            if (modelId === data.current_model) {
                option.selected = true;
            }
            
            modelSelect.appendChild(option);
        });
        
        modelSelect.disabled = false;
    } catch (error) {
        console.error('Failed to load models:', error);
        modelSelect.innerHTML = '<option>Error loading models</option>';
        
        // Retry after 2 seconds
        setTimeout(loadAvailableModels, 2000);
    }
}

// Handle model change
modelSelect.addEventListener('change', async (e) => {
    const selectedModel = e.target.value;
    
    if (isLoadingModel) {
        return;
    }
    
    isLoadingModel = true;
    modelSelect.disabled = true;
    sendButton.disabled = true;
    messageInput.disabled = true;
    
    // Show loading message
    const loadingMsg = addMessage(`🔄 Loading ${selectedModel}... Please wait, this may take a minute.`, 'loading');
    
    try {
        const response = await fetch('/api/models/load', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ model: selectedModel })
        });
        
        const result = await response.json();
        
        // Remove loading message
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
        console.log('WebSocket connected');
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
        console.log('WebSocket disconnected');
        updateConnectionStatus('disconnected', 'Disconnected');
        sendButton.disabled = true;
        
        // Attempt to reconnect after 3 seconds
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
    
    return messageDiv; // Return element for potential removal
}

// Show typing indicator
function showTypingIndicator(text) {
    if (!typingMessageElement) {
        typingMessageElement = document.createElement('div');
        typingMessageElement.className = 'message typing';
        messagesContainer.appendChild(typingMessageElement);
    }
    typingMessageElement.textContent = text;
    scrollToBottom();
}

// Remove typing indicator
function removeTypingIndicator() {
    if (typingMessageElement) {
        typingMessageElement.remove();
        typingMessageElement = null;
    }
}

// Scroll to bottom of chat
function scrollToBottom() {
    messagesContainer.parentElement.scrollTop = messagesContainer.parentElement.scrollHeight;
}

// Send message
function sendMessage() {
    const message = messageInput.value.trim();
    
    if (!message || !ws || ws.readyState !== WebSocket.OPEN) {
        return;
    }
    
    // Send message to server
    ws.send(JSON.stringify({ message }));
    
    // Clear input
    messageInput.value = '';
    messageInput.focus();
}

// Event listeners
sendButton.addEventListener('click', sendMessage);

messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

// Initialize connection when page loads
document.addEventListener('DOMContentLoaded', () => {
    loadAvailableModels();
    connect();
});
