// // DOM Elements
// const userInput = document.getElementById('userInput');
// const askBtn = document.getElementById('askBtn');
// const welcomeSection = document.getElementById('welcomeSection');
// const suggestionsSection = document.getElementById('suggestionsSection');
// const chatContainer = document.getElementById('chatContainer');
// const clearHistoryBtn = document.getElementById('clearHistoryBtn');

// // State Management
// let chatHistory = JSON.parse(localStorage.getItem('chat_history')) || [];

// // Initialize
// document.addEventListener('DOMContentLoaded', () => {
//     if (chatHistory.length > 0) {
//         showChatMode();
//         renderHistory();
//     } else {
//         showWelcomeMode();
//     }
// });

// // 1. View Toggles
// function showWelcomeMode() {
//     welcomeSection.classList.remove('hidden');
//     suggestionsSection.classList.remove('hidden');
//     chatContainer.classList.add('hidden');
//     // Hide clear button if no history
//     clearHistoryBtn.style.display = 'none'; 
// }

// function showChatMode() {
//     welcomeSection.classList.add('hidden');
//     suggestionsSection.classList.add('hidden');
//     chatContainer.classList.remove('hidden');
//     clearHistoryBtn.style.display = 'flex';
// }

// // 2. Rendering Logic
// function renderHistory() {
//     chatContainer.innerHTML = ''; // Clear current view
    
//     chatHistory.forEach(msg => {
//         appendMessageToUI(msg.role, msg.content, false);
//     });
    
//     scrollToBottom();
// }

// function appendMessageToUI(role, text, isLoading = false) {
//     const wrapper = document.createElement('div');
//     wrapper.className = `message-wrapper ${role}`;

//     let contentHtml = text;
    
//     // Add Avatar for AI
//     if (role === 'ai') {
//         const avatar = document.createElement('div');
//         avatar.className = 'avatar ai';
//         avatar.innerHTML = '✨'; // Sparkle icon
//         wrapper.appendChild(avatar);
//     }

//     const bubble = document.createElement('div');
//     bubble.className = `bubble ${role}`;
    
//     if (isLoading) {
//         bubble.innerHTML = '<span class="loading-dots">Thinking...</span>';
//         wrapper.id = "loading-bubble"; // Tag it to remove later
//     } else {
//         bubble.textContent = text;
//     }

//     wrapper.appendChild(bubble);
//     chatContainer.appendChild(wrapper);
//     scrollToBottom();
// }

// function scrollToBottom() {
//     chatContainer.scrollTop = chatContainer.scrollHeight;
// }

// // 3. Action Logic
// function addToHistory(role, content) {
//     chatHistory.push({ role, content });
//     localStorage.setItem('chat_history', JSON.stringify(chatHistory));
// }

// // Clear History
// clearHistoryBtn.addEventListener('click', () => {
//     if(confirm("Are you sure you want to clear your chat history?")) {
//         localStorage.removeItem('chat_history');
//         chatHistory = [];
//         showWelcomeMode();
//         userInput.value = '';
//     }
// });

// // Suggestions Click
// window.fillInput = function(text) {
//     userInput.value = text;
//     userInput.focus();
// }

// // Handle Ask
// askBtn.addEventListener('click', handleUserQuery);

// // Allow Enter key to submit
// userInput.addEventListener('keydown', (e) => {
//     if (e.key === 'Enter' && !e.shiftKey) {
//         e.preventDefault();
//         handleUserQuery();
//     }
// });

// async function handleUserQuery() {
//     const text = userInput.value.trim();
//     if (!text) return;

//     // 1. Switch UI to chat mode immediately
//     showChatMode();

//     // 2. Add User Message
//     appendMessageToUI('user', text);
//     addToHistory('user', text);
//     userInput.value = '';

//     // 3. Add Loading Bubble
//     appendMessageToUI('ai', '', true);

//     try {
//         // 4. API Request
//         const response = await fetch('http://127.0.0.1:5000/api/query', {
//             method: 'POST',
//             headers: { 'Content-Type': 'application/json' },
//             body: JSON.stringify({ query: text })
//         });

//         const data = await response.json();
        
//         // Remove loading bubble
//         const loadingBubble = document.getElementById('loading-bubble');
//         if (loadingBubble) loadingBubble.remove();

//         // 5. Display AI Response
//         const aiText = data.error ? "Error: " + data.error : data.response;
//         appendMessageToUI('ai', aiText);
//         addToHistory('ai', aiText);

//     } catch (error) {
//         const loadingBubble = document.getElementById('loading-bubble');
//         if (loadingBubble) loadingBubble.remove();
        
//         const errorMsg = "Could not connect to the server.";
//         appendMessageToUI('ai', errorMsg);
//         // We generally don't save connection errors to history, but you can if you want.
//     }
// }

// DOM Elements
const userInput = document.getElementById('userInput');
const askBtn = document.getElementById('askBtn');
const welcomeSection = document.getElementById('welcomeSection');
const suggestionsSection = document.getElementById('suggestionsSection');
const chatContainer = document.getElementById('chatContainer');
const clearHistoryBtn = document.getElementById('clearHistoryBtn');

// State Management: Load existing history or start fresh
let chatHistory = JSON.parse(localStorage.getItem('chat_history')) || [];

// Initialize view based on history existence
document.addEventListener('DOMContentLoaded', () => {
    if (chatHistory.length > 0) {
        showChatMode();
        renderHistory();
    } else {
        showWelcomeMode();
    }
});

// --- View Toggles ---

function showWelcomeMode() {
    welcomeSection.classList.remove('hidden');
    suggestionsSection.classList.remove('hidden');
    chatContainer.classList.add('hidden');
    clearHistoryBtn.style.display = 'none'; 
}

function showChatMode() {
    welcomeSection.classList.add('hidden');
    suggestionsSection.classList.add('hidden');
    chatContainer.classList.remove('hidden');
    clearHistoryBtn.style.display = 'flex';
}

// --- Rendering Logic ---

function renderHistory() {
    chatContainer.innerHTML = ''; // Clean the container before rendering
    
    chatHistory.forEach(msg => {
        createMessageElement(msg.role, msg.content, false);
    });
    
    scrollToBottom();
}

function createMessageElement(role, text, isLoading = false) {
    const wrapper = document.createElement('div');
    wrapper.className = `message-wrapper ${role}`;

    // Add Avatar for AI only
    if (role === 'ai') {
        const avatar = document.createElement('div');
        avatar.className = 'avatar ai';
        avatar.innerHTML = '✨'; 
        wrapper.appendChild(avatar);
    }

    const bubble = document.createElement('div');
    bubble.className = `bubble ${role}`;
    
    if (isLoading) {
        bubble.innerHTML = '<span class="loading-dots">Thinking...</span>';
        wrapper.id = "loading-bubble"; // Tag so we can remove it later
    } else {
        bubble.textContent = text;
    }

    wrapper.appendChild(bubble);
    chatContainer.appendChild(wrapper);
    scrollToBottom();
}

function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// --- Core Logic ---

function saveToHistory(role, content) {
    // 1. Update the in-memory array
    chatHistory.push({ role, content });
    
    // 2. Save the updated array to localStorage
    localStorage.setItem('chat_history', JSON.stringify(chatHistory));
}

// *** FIXED CLEAR LOGIC ***
clearHistoryBtn.addEventListener('click', () => {
    if(confirm("Are you sure you want to clear your chat history?")) {
        // 1. Clear the localStorage
        localStorage.removeItem('chat_history');
        
        // 2. CRITICAL: Clear the in-memory array variable
        chatHistory = [];
        
        // 3. Clear the UI
        chatContainer.innerHTML = '';
        userInput.value = '';
        
        // 4. Return to Welcome Screen
        showWelcomeMode();
    }
});

// Helper for suggestion chips
window.fillInput = function(text) {
    userInput.value = text;
    userInput.focus();
}

// Handle User Submission
askBtn.addEventListener('click', handleUserQuery);

// Allow Enter key to submit
userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleUserQuery();
    }
});

async function handleUserQuery() {
    const text = userInput.value.trim();
    if (!text) return;

    // Switch UI to chat mode
    showChatMode();

    // 1. Add User Message
    createMessageElement('user', text);
    saveToHistory('user', text);
    userInput.value = '';

    // 2. Add Loading Indicator
    createMessageElement('ai', '', true);

    try {
        // 3. Call API
        const response = await fetch('http://127.0.0.1:5000/api/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: text })
        });

        const data = await response.json();
        
        // Remove loading bubble
        const loadingBubble = document.getElementById('loading-bubble');
        if (loadingBubble) loadingBubble.remove();

        // 4. Display AI Response
        const aiText = data.error ? "Error: " + data.error : data.response;
        createMessageElement('ai', aiText);
        saveToHistory('ai', aiText);

    } catch (error) {
        // Handle connection errors
        const loadingBubble = document.getElementById('loading-bubble');
        if (loadingBubble) loadingBubble.remove();
        
        const errorMsg = "Could not connect to the server.";
        createMessageElement('ai', errorMsg);
        // We usually don't save error messages to history, but you can if you like.
    }
}