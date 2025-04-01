// --- Get Element References ---
const messageArea = document.getElementById('message-area');
const messageInput = document.getElementById('messageText'); 
const messageForm = document.getElementById('messageForm');
const sendButton = document.getElementById('sendButton');
const cancelButton = document.getElementById('cancelButton');
const spinner = document.getElementById('spinner'); 
const themeToggleButton = document.getElementById('theme-toggle-button');
const rootHtmlElement = document.documentElement; 

// New Upload Elements
const uploadTriggerButton = document.getElementById('uploadTriggerButton');
const popupMenu = document.getElementById('popupMenu');
const popupUploadOption = document.getElementById('popupUploadOption');
const fileInput = document.getElementById('fileInput'); 
const dynamicUploadStatus = document.getElementById('dynamicUploadStatus'); 

let websocket = null;
let isWaitingForBot = false;
let isUploading = false; // Flag to prevent double uploads

function applyTheme(theme) {
    if (theme === 'dark') {
        rootHtmlElement.classList.add('dark-mode');
        themeToggleButton?.setAttribute('aria-pressed', 'true'); 
    } else {
        rootHtmlElement.classList.remove('dark-mode');
        themeToggleButton?.setAttribute('aria-pressed', 'false');
    }

    try {
        localStorage.setItem('theme', theme);
    } catch (e) {
        console.error("LocalStorage not available or failed to set theme:", e);
    }
}

// --- Function to Toggle Theme ---
function toggleTheme() {
    const currentIsDark = rootHtmlElement.classList.contains('dark-mode');
    const newTheme = currentIsDark ? 'light' : 'dark';
    applyTheme(newTheme);
    console.log(`Theme toggled to: ${newTheme}`);
}

// --- Initial Theme Setup ---
function initializeTheme() {
    try {
        const theme = localStorage.getItem('theme');
        const isOsDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        const currentTheme = theme ? theme : (isOsDark ? 'dark' : 'light');

         if(themeToggleButton) {
            themeToggleButton.setAttribute('aria-pressed', currentTheme === 'dark' ? 'true' : 'false');
         }
         console.log(`Initializing theme logic. Current effective theme: ${currentTheme}`);

    } catch (e) {
        console.error("Failed to initialize theme state:", e);
         if(themeToggleButton) themeToggleButton.setAttribute('aria-pressed', 'false'); // Default aria
    }
}

// --- Add Event Listener for Toggle Button ---
if (themeToggleButton) {
    themeToggleButton.addEventListener('click', toggleTheme);
}

if (messageInput) {
    messageInput.addEventListener('keydown', function(event) {
        if (event.key === 'Enter') {
            if (!event.shiftKey) {
                // Prevent default Enter behavior
                event.preventDefault();

                // Check if the message only contains whitespace or is empty
                if (messageInput.value.trim() === '') {
                    // If message is empty, submit the form
                    messageForm.requestSubmit();
                } else {
                    // Add a newline if the last line contains content
                    const lastLineEmpty = messageInput.value.endsWith('\n');
                    
                    if (lastLineEmpty) {
                        // Submit if last line is empty
                        messageForm.requestSubmit();
                    } else {
                        // Otherwise, add a newline
                        messageInput.value += '\n';
                        adjustTextareaHeight();  // Adjust height for new line
                    }
                }
            }
        }
    });

    messageInput.addEventListener('input', adjustTextareaHeight);
}

function connectWebSocket() {
    console.log("Attempting to connect WebSocket to:", wsUrl);
    if (websocket && websocket.readyState === WebSocket.OPEN) return;
    websocket = new WebSocket(wsUrl);

    websocket.onopen = function(event) {
        console.log("WebSocket connection established");
        addMessage("Bot: Ask me anything!", "bot-message"); 
        resetUIState();
    };

    websocket.onmessage = function(event) {
        console.log("Raw data received:", event.data);
        let messageText = event.data;
        let messageClass = messageText.startsWith("Bot:") ? "bot-message" : "user-message"; 
        addMessage(messageText.replace(/^Bot:\s*/, ''), messageClass); 

        if (messageClass === 'bot-message' && isWaitingForBot) {
           resetUIState();
        }
    };
    websocket.onerror = function(event) { /* ... keep error handling ... */ };
    websocket.onclose = function(event) { /* ... keep close handling ... */ };
}

// --- Add Message ---
function addMessage(message, cssClass) {
    const messageWrapper = document.createElement('div');
    messageWrapper.className = `message-wrapper ${cssClass.includes('user') ? 'user' : 'bot'}`;
    const iconDiv = document.createElement('div');
    iconDiv.className = 'icon';
    messageWrapper.appendChild(iconDiv); 

    // --- Main Message Bubble Container ---
    const messageContentContainer = document.createElement('div');
    messageContentContainer.className = `message ${cssClass}`; // Base message bubble styles

    // --- Split message into text and $$formula$$ parts ---
    const parts = message.split(/(\$\$[\s\S]*?\$\$)/g);
    const filteredParts = parts.filter(part => part && part.trim() !== '');

    if (filteredParts.length === 0 && message.trim() !== '') {
         filteredParts.push(message);
    } else if (filteredParts.length === 0 && message.trim() === '') {
         return; 
    }

    // --- Process Each Part and Create Segment Divs ---
    filteredParts.forEach(part => {
        const segmentElement = document.createElement('div'); 

        if (part.startsWith('$$') && part.endsWith('$$')) {
            // It's a display math block
            segmentElement.className = 'message-segment message-formula-block';
            segmentElement.textContent = part; // Set raw text for KaTeX
        } else {
            // It's a regular text block (might contain $inline$ math)
            segmentElement.className = 'message-segment message-text-block';
            segmentElement.textContent = part; // Set raw text for KaTeX
        }

        // Append the segment div to the message content container
        messageContentContainer.appendChild(segmentElement);

        // Render KaTeX within this specific segment *after* appending
        // This ensures context and handles both display and inline math within segments
        try {
            if (typeof renderMathInElement === 'function') {
                renderMathInElement(segmentElement, {
                    delimiters: [
                        {left: "$$", right: "$$", display: true}, // Render $$ as display
                        {left: "$", right: "$", display: false}, // Render $ as inline
                        {left: "\\(", right: "\\)", display: false},
                        {left: "\\[", right: "\\]", display: true}
                    ],
                    throwOnError: false
                });
            } else {
                 console.warn("renderMathInElement not available for segment.");
            }
        } catch (error) {
            console.error("KaTeX rendering failed for segment:", error);
        }
    });

    // Append the container holding all segments to the wrapper
    messageWrapper.appendChild(messageContentContainer);

    // --- Add Timestamp ---
    const timestampSpan = document.createElement('span');
    timestampSpan.className = 'timestamp';
    timestampSpan.style.alignSelf = cssClass.includes('user') ? 'flex-end' : 'flex-start';
    timestampSpan.style.marginTop = '0.3rem';
    timestampSpan.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    messageWrapper.appendChild(timestampSpan);

    // --- Append the whole wrapper to the message area ---
    messageArea.appendChild(messageWrapper);

    // --- Scroll to bottom ---
    messageArea.scrollTo({ top: messageArea.scrollHeight, behavior: 'smooth' });
}

// --- Send Chat Message ---
function sendMessage(event) {
    event.preventDefault();
    if (isWaitingForBot || isUploading) return; // Don't send if waiting or uploading

    const message = messageInput.value.trim();
    if (message && websocket && websocket.readyState === WebSocket.OPEN) {
        console.log("Setting UI to waiting state...");
        isWaitingForBot = true;
        messageInput.disabled = true;
        uploadTriggerButton.disabled = true; // Disable upload during send
        sendButton.disabled = true;
        sendButton.innerHTML = spinner.outerHTML; // Replace button content with spinner
        cancelButton.style.display = 'inline-flex';
        
        console.log(">>> Sending message:", message);
        websocket.send(message);
        console.log("<<< websocket.send called.");
        addMessage(`You: ${message}`, "user-message");

        messageInput.value = '';
        adjustTextareaHeight(); // Reset height after sending
    } else { /* ... error handling ... */ }
}

// --- Reset UI State ---
function resetUIState(cancelled = false) {
    isWaitingForBot = false;
    messageInput.disabled = false;
    if (!isUploading) {
        uploadTriggerButton.disabled = false;
        sendButton.disabled = false;
    }

    sendButton.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-arrow-up"><line x1="12" y1="19" x2="12" y2="5"></line><polyline points="5 12 12 5 19 12"></polyline></svg>`;
    cancelButton.style.display = 'none';

    if (cancelled) addMessage("Bot: Processing cancelled.", "bot-message error"); // Maybe make this less obtrusive
    messageInput.focus();
}

// --- Cancel Button Listener ---
cancelButton.addEventListener('click', () => {
    if (isWaitingForBot) {
        console.log("User cancelled request.");
        resetUIState(true);
    }
});

if (uploadTriggerButton && popupMenu) {
    uploadTriggerButton.addEventListener('click', (event) => {
        event.stopPropagation(); 
        if (isUploading || isWaitingForBot) return; // Don't open if busy

        const isActive = popupMenu.classList.contains('popup-active');
        if (isActive) {
            closePopupMenu();
        } else {
            openPopupMenu();
        }
    });
}

if (popupUploadOption && fileInput) {
    popupUploadOption.addEventListener('click', () => {
        console.log("Upload file option clicked");
        fileInput.click(); // Trigger the hidden file input
        closePopupMenu(); // Close menu after clicking option
    });
}

document.addEventListener('click', (event) => {
    if (popupMenu && popupMenu.classList.contains('popup-active')) {
        // Check if the click was outside the menu AND outside the trigger button
        if (!popupMenu.contains(event.target) && !uploadTriggerButton.contains(event.target)) {
            closePopupMenu();
        }
    }
});

// Helper functions for popup state
function openPopupMenu() {
    if (!popupMenu) return;
    popupMenu.classList.add('popup-active');
    uploadTriggerButton.setAttribute('aria-expanded', 'true');
}

function closePopupMenu() {
    if (!popupMenu) return;
    popupMenu.classList.remove('popup-active');
    uploadTriggerButton.setAttribute('aria-expanded', 'false');
}

// 3. Function to perform the actual upload
async function uploadFile(file) {
    if (isUploading) return; // Prevent concurrent uploads

    const formData = new FormData();
    formData.append('file', file); // Key 'file' must match FastAPI parameter

    setDynamicUploadStatus(`Uploading "${file.name}"...`, "info");
    isUploading = true;
    uploadTriggerButton.disabled = true; // Disable while uploading
    sendButton.disabled = true;         // Disable send while uploading

    try {
        const response = await fetch('/data/upload', { method: 'POST', body: formData });
        const result = await response.json();

        if (response.ok && response.status === 202) {
            setDynamicUploadStatus(`Processing "${result.filename}"...`, "success");
            setTimeout(() => setDynamicUploadStatus(""), 5000);
        } else {
            const errorDetail = result.detail || `Server error ${response.status}`;
            setDynamicUploadStatus(`Upload failed: ${errorDetail}`, "error");
             setTimeout(() => setDynamicUploadStatus(""), 8000); // Keep error longer
        }
    } catch (error) {
        console.error("Upload error:", error);
        setDynamicUploadStatus(`Upload failed: ${error.message || 'Network error'}`, "error");
        setTimeout(() => setDynamicUploadStatus(""), 8000);
    } finally {
        isUploading = false; // Re-enable uploading
        // Only re-enable buttons if not waiting for bot response
        if (!isWaitingForBot) {
             uploadTriggerButton.disabled = false;
             sendButton.disabled = false;
        }
    }
}

// 4. Function to update the dynamic status message
function setDynamicUploadStatus(message, type = "") { // type: info, success, error
    if (dynamicUploadStatus) {
        dynamicUploadStatus.textContent = message;
        dynamicUploadStatus.className = `upload-status-dynamic ${type}`;
    }
}

// --- Textarea Auto-Resize (Optional) ---
function adjustTextareaHeight() {
    messageInput.style.height = 'auto'; // Reset height
    let scrollHeight = messageInput.scrollHeight;

    messageInput.style.height = `${scrollHeight}px`;
}

if(messageInput) {
    messageInput.addEventListener('input', adjustTextareaHeight);
    // adjustTextareaHeight();
}

// --- Initial Setup ---
initializeTheme(); // Set initial theme based on localStorage or OS preference
connectWebSocket();
