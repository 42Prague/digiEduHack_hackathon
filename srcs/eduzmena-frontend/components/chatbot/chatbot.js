// Chatbot WebSocket client with JSON response processing

// Configuration
const CONFIG = {
    wsUrl: "ws://localhost:8000/ws/chat",
    // JSON response field paths to extract (tried in order)
    responseFields: [
        "response",      // e.g., { response: "..." }
        "message",       // e.g., { message: "..." }
        "text",          // e.g., { text: "..." }
        "content",       // e.g., { content: "..." }
        "data.response", // e.g., { data: { response: "..." } }
        "data.message",  // e.g., { data: { message: "..." } }
        "result",        // e.g., { result: "..." }
        "answer"         // e.g., { answer: "..." }
    ],
    // Field to extract error messages from
    errorFields: ["error", "error_message", "errorMessage", "message"],
    // Show connection status
    showStatus: true
};

const chatWindow = document.getElementById("chat-window");
const chatInput = document.getElementById("chat-input");
const sendBtn = document.getElementById("send-btn");

let socket = null;
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;
const reconnectDelay = 3000;

/**
 * Extract value from nested object using dot notation path
 * @param {Object} obj - Object to extract from
 * @param {string} path - Dot notation path (e.g., "data.message")
 * @returns {*} Extracted value or null
 */
function extractNestedValue(obj, path) {
    const keys = path.split('.');
    let value = obj;
    
    for (const key of keys) {
        if (value && typeof value === 'object' && key in value) {
            value = value[key];
        } else {
            return null;
        }
    }
    
    return value;
}

/**
 * Extract response text from JSON object
 * @param {Object} jsonData - Parsed JSON object
 * @returns {string|null} Extracted response text or null
 */
function extractResponse(jsonData) {
    // Try each configured field path
    for (const field of CONFIG.responseFields) {
        const value = extractNestedValue(jsonData, field);
        if (value !== null && value !== undefined) {
            // Convert to string if needed
            if (typeof value === 'string') {
                return value;
            } else if (typeof value === 'object') {
                // If it's an object, try to stringify or extract further
                return JSON.stringify(value, null, 2);
            } else {
                return String(value);
            }
        }
    }
    
    // If no field matched, return the whole object as string
    return JSON.stringify(jsonData, null, 2);
}

/**
 * Extract error message from JSON object
 * @param {Object} jsonData - Parsed JSON object
 * @returns {string|null} Error message or null
 */
function extractError(jsonData) {
    for (const field of CONFIG.errorFields) {
        const value = extractNestedValue(jsonData, field);
        if (value !== null && value !== undefined) {
            return String(value);
        }
    }
    return "An error occurred";
}

/**
 * Process WebSocket message
 * @param {string|Object} data - Raw message data
 * @returns {Object} Processed message with type and content
 */
function processMessage(data) {
    // Try to parse as JSON
    let jsonData;
    try {
        jsonData = typeof data === 'string' ? JSON.parse(data) : data;
    } catch (e) {
        // Not JSON, return as plain text
        return {
            type: 'message',
            content: String(data),
            raw: data
        };
    }

    // Check if it's an error
    if (jsonData.error || jsonData.status === 'error' || jsonData.type === 'error') {
        return {
            type: 'error',
            content: extractError(jsonData),
            raw: jsonData
        };
    }

    // Extract response content
    const content = extractResponse(jsonData);
    
    return {
        type: jsonData.type || 'message',
        content: content,
        raw: jsonData
    };
}

/**
 * Append message to chat window
 * @param {string} text - Message text
 * @param {string} sender - Sender type ('user' or 'bot')
 * @param {string} type - Message type ('message', 'error', 'system')
 */
function appendMessage(text, sender, type = 'message') {
    const div = document.createElement("div");
    div.classList.add("message", sender);
    
    if (type === 'error') {
        div.classList.add("error");
    }
    
    // Escape HTML to prevent XSS
    const textNode = document.createTextNode(text);
    div.appendChild(textNode);
    
    chatWindow.appendChild(div);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

/**
 * Update connection status
 * @param {string} status - Status text
 * @param {string} type - Status type ('connected', 'disconnected', 'connecting', 'error')
 */
function updateStatus(status, type = 'info') {
    if (!CONFIG.showStatus) return;
    
    // Remove existing status messages
    const existingStatus = chatWindow.querySelector('.status-message');
    if (existingStatus) {
        existingStatus.remove();
    }
    
    const statusDiv = document.createElement("div");
    statusDiv.classList.add("message", "system", "status-message");
    statusDiv.textContent = `[${status}]`;
    chatWindow.appendChild(statusDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

/**
 * Connect to WebSocket server
 */
function connect() {
    try {
        socket = new WebSocket(CONFIG.wsUrl);

        socket.onopen = () => {
            console.log("Connected to WebSocket server");
            reconnectAttempts = 0;
            updateStatus("Connected", "connected");
        };

        socket.onerror = (err) => {
            console.error("WebSocket error:", err);
            updateStatus("Connection error", "error");
        };

        socket.onclose = () => {
            console.log("WebSocket disconnected");
            updateStatus("Disconnected", "disconnected");
            
            // Attempt to reconnect
            if (reconnectAttempts < maxReconnectAttempts) {
                reconnectAttempts++;
                setTimeout(() => {
                    console.log(`Reconnecting... (attempt ${reconnectAttempts}/${maxReconnectAttempts})`);
                    updateStatus(`Reconnecting... (${reconnectAttempts}/${maxReconnectAttempts})`, "connecting");
                    connect();
                }, reconnectDelay);
            } else {
                updateStatus("Connection failed. Please refresh the page.", "error");
            }
        };

        socket.onmessage = (event) => {
            try {
                const processed = processMessage(event.data);
                
                if (processed.type === 'error') {
                    appendMessage(processed.content, "bot", "error");
                } else {
                    appendMessage(processed.content, "bot", processed.type);
                }
            } catch (error) {
                console.error("Error processing message:", error);
                appendMessage("Error processing response", "bot", "error");
            }
        };
    } catch (error) {
        console.error("Error connecting to WebSocket:", error);
        updateStatus("Connection failed", "error");
    }
}

/**
 * Send message to WebSocket server
 */
function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;
    
    if (!socket || socket.readyState !== WebSocket.OPEN) {
        appendMessage("Not connected to server. Please wait...", "system", "error");
        return;
    }

    // Send message (can be plain text or JSON)
    try {
        // Option 1: Send as plain text
        socket.send(text);
        
        // Option 2: Send as JSON (uncomment if your backend expects JSON)
        // socket.send(JSON.stringify({ message: text, type: "user_message" }));
        
        appendMessage(text, "user");
        chatInput.value = "";
    } catch (error) {
        console.error("Error sending message:", error);
        appendMessage("Error sending message", "system", "error");
    }
}

// Initialize
if (chatWindow && chatInput && sendBtn) {
    // Connect to WebSocket
    connect();
    
    // Track if first message sent
    let firstMessage = true;
    
    // Wrapper function to clear status on first message
    function handleSendMessage() {
        if (firstMessage) {
            const statusMsg = chatWindow.querySelector('.status-message');
            if (statusMsg) statusMsg.remove();
            firstMessage = false;
        }
        sendMessage();
    }
    
    // Event listeners
    sendBtn.addEventListener("click", handleSendMessage);
    
    chatInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });
} else {
    console.error("Chatbot elements not found");
}
