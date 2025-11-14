// Chatbot WebSocket client with JSON response processing

const CONFIG = {
    wsUrl: "ws://localhost:8000/chat/",
    // Fields to extract from JSON response (tried in order)
    responseFields: ["response", "message", "text", "content", "data.response", "data.message", "result", "answer"],
    errorFields: ["error", "error_message", "errorMessage", "message"]
};

const chatWindow = document.getElementById("chat-window");
const chatInput = document.getElementById("chat-input");
const sendBtn = document.getElementById("send-btn");

let socket = null;
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;
let currentBotMessage = null; // Current bot message element being streamed to
let currentRole = null; // Track current role to detect role changes
let thinkingMessage = null; // "Thinking..." message element
let thinkingInterval = null; // Interval for animating thinking dots

/**
 * Get value from object using dot notation path
 */
function getValue(obj, path) {
    return path.split('.').reduce((current, key) => current?.[key], obj);
}

/**
 * Extract response text from JSON
 */
function extractResponse(json) {
    // Try each field
    for (const field of CONFIG.responseFields) {
        const value = getValue(json, field);
        if (value != null) {
            return typeof value === 'string' ? value : JSON.stringify(value, null, 2);
        }
    }
    // Fallback: return whole object as JSON
    return JSON.stringify(json, null, 2);
}

/**
 * Extract error message from JSON
 */
function extractError(json) {
    for (const field of CONFIG.errorFields) {
        const value = getValue(json, field);
        if (value != null) return String(value);
    }
    return "An error occurred";
}

/**
 * Process WebSocket message
 */
function processMessage(data) {
    try {
        const json = typeof data === 'string' ? JSON.parse(data) : data;
        
        // Check for errors
        if (json.error || json.status === 'error' || json.type === 'error') {
            return { type: 'error', content: extractError(json) };
        }
        
        // Extract response
        return { type: 'message', content: extractResponse(json) };
    } catch (e) {
        // Not JSON, return as plain text
        return { type: 'message', content: String(data) };
    }
}

/**
 * Create a new message element
 */
function createMessageElement(sender, isError = false) {
    const div = document.createElement("div");
    div.className = `message ${sender}${isError ? ' error' : ''}`;
    chatWindow.appendChild(div);
    chatWindow.scrollTop = chatWindow.scrollHeight;
    return div;
}

/**
 * Add complete message to chat window
 */
function appendMessage(text, sender, isError = false) {
    const div = createMessageElement(sender, isError);
    div.textContent = text;
}

/**
 * Show "Thinking..." message with animated dots
 */
function showThinking() {
    if (!thinkingMessage) {
        thinkingMessage = createMessageElement("bot");
        thinkingMessage.style.opacity = "0.6";
        thinkingMessage.style.fontStyle = "italic";
        
        // Start animated dots
        let dotCount = 0;
        thinkingInterval = setInterval(() => {
            dotCount = (dotCount % 3) + 1; // Cycle through 1, 2, 3
            thinkingMessage.textContent = "Thinking" + ".".repeat(dotCount);
        }, 500); // Update every 500ms
    }
}

/**
 * Remove "Thinking..." message
 */
function removeThinking() {
    if (thinkingInterval) {
        clearInterval(thinkingInterval);
        thinkingInterval = null;
    }
    if (thinkingMessage) {
        thinkingMessage.remove();
        thinkingMessage = null;
    }
}

/**
 * Append text to current streaming message (or create new one if role changed)
 */
function appendToStreamingMessage(text, role = null, sender = "bot") {
    // Check if role changed - if so, start a new message
    if (role && role !== currentRole && currentBotMessage) {
        // Finish current message and start new one
        currentBotMessage = null;
        currentRole = role;
    } else if (role) {
        currentRole = role;
    }
    
    // Remove thinking message when we start receiving content
    removeThinking();
    
    // Create new message if needed
    if (!currentBotMessage) {
        currentBotMessage = createMessageElement(sender);
    }
    
    // Handle tools role specially
    if (role === "tools") {
        // Don't append the dump, just show that it looked through local data
        if (!currentBotMessage.textContent.includes("Looping through local data")) {
            currentBotMessage.textContent = "Looping through local data...";
        }
    } else {
        // Append text normally
        currentBotMessage.textContent += text;
    }
    
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

/**
 * Finish current streaming message
 */
function finishStreamingMessage() {
    removeThinking();
    currentBotMessage = null;
    currentRole = null;
}

/**
 * Show connection status
 */
function showStatus(text) {
    const div = document.createElement("div");
    div.className = "message system status-message";
    div.textContent = `[${text}]`;
    chatWindow.appendChild(div);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

/**
 * Connect to WebSocket
 */
function connect() {
    try {
        socket = new WebSocket(CONFIG.wsUrl);

        socket.onopen = () => {
            console.log("Connected");
            reconnectAttempts = 0;
            showStatus("Connected");
        };

        socket.onerror = () => showStatus("Connection error");

        socket.onclose = () => {
            showStatus("Disconnected");
            if (reconnectAttempts < maxReconnectAttempts) {
                reconnectAttempts++;
                setTimeout(() => {
                    showStatus(`Reconnecting... (${reconnectAttempts}/${maxReconnectAttempts})`);
                    connect();
                }, 3000);
            } else {
                showStatus("Connection failed. Please refresh.");
            }
        };

        socket.onmessage = (event) => {
            try {
                const json = typeof event.data === 'string' ? JSON.parse(event.data) : event.data;
                
                // Check for "done" event (end of stream) - don't display it, just finish
                if (json.event === 'done') {
                    finishStreamingMessage();
                    return; // Exit early, don't process this message
                }
                
                // Get role from the message (ModelResponse has 'role' field)
                const role = json.role || null;
                
                // Extract text from chunk (ModelResponse has 'content' field)
                // The backend sends: { role: "...", content: "text chunk" }
                let chunkText = null;
                
                // Handle tools role - don't show the dump
                if (role === "tools") {
                    // Just show that it's looking through local data
                    appendToStreamingMessage("", role);
                    return;
                }
                
                // Try to get content directly (most common case)
                if (json.content != null) {
                    chunkText = String(json.content);
                } else {
                    // Fallback to extractResponse for other formats
                    chunkText = extractResponse(json);
                }
                
                // Append to current streaming message (joins all chunks together)
                // Role changes will trigger new message creation
                if (chunkText) {
                    appendToStreamingMessage(chunkText, role);
                }
            } catch (e) {
                console.error("Error processing message:", e);
                // Only append if it's not the done event
                const dataStr = String(event.data);
                if (!dataStr.includes('"event"') || !dataStr.includes('"done"')) {
                    appendToStreamingMessage(dataStr);
                }
            }
        };
    } catch (error) {
        console.error("Connection error:", error);
        showStatus("Connection failed");
    }
}

/**
 * Send message
 */
function sendMessage() {
    const text = chatInput.value.trim();
    if (!text || !socket || socket.readyState !== WebSocket.OPEN) return;

    // Finish any previous streaming message
    finishStreamingMessage();
    
    // Send message to server
    socket.send(text);
    
    // Show user message
    appendMessage(text, "user");
    chatInput.value = "";
    
    // Remove status on first message
    const status = chatWindow.querySelector('.status-message');
    if (status) status.remove();
    
    // Show "Thinking..." while waiting for response
    showThinking();
    
    // Prepare for new bot response (will be created when first chunk arrives)
}

// Initialize
if (chatWindow && chatInput && sendBtn) {
    connect();
    sendBtn.addEventListener("click", sendMessage);
    chatInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
} else {
    console.error("Chatbot elements not found");
}
