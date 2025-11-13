const chatWindow = document.getElementById("chat-window");
const chatInput = document.getElementById("chat-input");
const sendBtn = document.getElementById("send-btn");

const socket = new WebSocket("ws://localhost:8000/ws/chat");

socket.onopen = () => {
    console.log("Connected to WebSocket server");
};

socket.onerror = (err) => {
    console.error("WebSocket error:", err);
};

socket.onmessage = (event) => {
    appendMessage(event.data, "bot");
};

function appendMessage(text, sender) {
    const div = document.createElement("div");
    div.classList.add("message", sender);
    div.textContent = text;
    chatWindow.appendChild(div);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

function sendMessage() {
    const text = chatInput.value.trim();
    if (!text || socket.readyState !== WebSocket.OPEN) return;

    appendMessage(text, "user");

    socket.send(text);
    chatInput.value = "";
}

sendBtn.addEventListener("click", sendMessage);

chatInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendMessage();
});
