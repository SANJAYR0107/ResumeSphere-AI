/**
 * network-dashboard.js
 * Handles UI interactions, WebSocket chat, and REST API feed fetching for Phase J.
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize Mock AI Connections / Team Matchmaker
    const mockConnections = [
        { name: "John Smith", role: "DevOps Engineer", match: "98%" },
        { name: "Sarah Lee", role: "Frontend Lead", match: "92%" },
        { name: "David Chen", role: "Data Scientist", match: "89%" }
    ];
    renderSuggestions(mockConnections);

    // 2. Initialize Social Feed
    const initialPosts = [
        { author: "Sarah Lee", role: "Frontend Lead at TechCorp", time: "2h ago", content: "Just passed the AWS Solutions Architect exam! Big thanks to the ResumeSphere Learning Hub for the resources. 🚀" },
        { author: "Recruiter Bob", role: "Talent Acquisition at FinTech", time: "4h ago", content: "We are actively hiring Senior Python Developers. Check out our Company Hub for more details!" }
    ];
    renderFeed(initialPosts);

    // 3. Handle Posting
    const postBtn = document.getElementById('btn-post');
    const postInput = document.getElementById('post-input');
    postBtn.addEventListener('click', () => {
        const text = postInput.value.trim();
        if (text) {
            addNewPost(text);
            postInput.value = '';
            showToast("Post published successfully to the Global Feed.");
        }
    });

    // 4. WebSocket Chat Implementation
    setupWebSocket();
});

// --- UI Rendering ---

function renderSuggestions(connections) {
    const container = document.getElementById('ai-team-matches');
    container.innerHTML = '';
    
    connections.forEach(conn => {
        const item = document.createElement('div');
        item.className = 'suggestion-item';
        item.innerHTML = `
            <img src="https://ui-avatars.com/api/?name=${conn.name}&background=random&color=fff" alt="${conn.name}">
            <div class="suggestion-item-info">
                <strong>${conn.name}</strong>
                <small>${conn.role} • <span style="color:var(--brand-primary)">${conn.match} Match</span></small>
            </div>
        `;
        container.appendChild(item);
    });
}

function renderFeed(posts) {
    const container = document.getElementById('feed-stream');
    posts.forEach(post => prependPostHTML(post, container));
}

function addNewPost(content) {
    const container = document.getElementById('feed-stream');
    const post = {
        author: "You",
        role: "Senior Software Engineer",
        time: "Just now",
        content: content
    };
    prependPostHTML(post, container);
}

function prependPostHTML(post, container) {
    const card = document.createElement('div');
    card.className = 'post-card glass-panel';
    card.innerHTML = `
        <div class="post-header">
            <img src="https://ui-avatars.com/api/?name=${post.author}&background=random&color=fff" alt="${post.author}">
            <div class="post-meta">
                <strong>${post.author}</strong>
                <small>${post.role} • ${post.time}</small>
            </div>
        </div>
        <div class="post-content">
            <p>${post.content}</p>
        </div>
        <div class="post-interaction">
            <span><i class='bx bx-like'></i> Like</span>
            <span><i class='bx bx-comment'></i> Comment</span>
            <span><i class='bx bx-share'></i> Share</span>
        </div>
    `;
    container.prepend(card);
}

// --- WebSocket Logic ---

function setupWebSocket() {
    // Generate a random user ID for this mock session
    const myUserId = "user_" + Math.floor(Math.random() * 10000);
    
    // Connect to the FastAPI WebSocket endpoint
    // Fallback to mock behavior if server is not running
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/network/ws/${myUserId}`;
    
    let ws;
    try {
        ws = new WebSocket(wsUrl);
        
        ws.onopen = () => {
            console.log("WebSocket connected globally.");
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            appendChatMessage(data.content, 'incoming');
        };

        ws.onclose = () => {
            console.log("WebSocket disconnected.");
        };
    } catch(e) {
        console.warn("WebSocket server not detected, using mock UI mode.");
    }

    // Chat UI Send
    const chatBtn = document.getElementById('chat-send-btn');
    const chatInput = document.getElementById('chat-input-box');
    
    const sendMessage = () => {
        const text = chatInput.value.trim();
        if (text) {
            appendChatMessage(text, 'outgoing');
            if (ws && ws.readyState === WebSocket.OPEN) {
                // Send broadcast message
                ws.send(JSON.stringify({ to: null, content: text }));
            } else {
                // Mock reply if no server
                setTimeout(() => {
                    appendChatMessage("AI Auto-reply: I'm currently offline, but the network got your message!", 'incoming');
                }, 1000);
            }
            chatInput.value = '';
        }
    };

    chatBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
}

function appendChatMessage(text, type) {
    const container = document.getElementById('chat-messages');
    const msg = document.createElement('div');
    msg.className = `msg-bubble ${type}`;
    msg.textContent = text;
    container.appendChild(msg);
    container.scrollTop = container.scrollHeight;
}

// --- Utils ---
function showToast(message) {
    const container = document.getElementById('toast-container') || document.body;
    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed; bottom: 20px; right: 20px;
        background: var(--brand-primary); color: white;
        padding: 1rem; border-radius: 8px; z-index: 9999;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    `;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}
