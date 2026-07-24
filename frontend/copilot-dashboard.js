/**
 * copilot-dashboard.js
 * Handles AI Agent Chat and Web Speech API for Voice commands.
 */

document.addEventListener('DOMContentLoaded', () => {
    
    // --- Chat Logic ---
    const chatInput = document.getElementById('copilot-input');
    const sendBtn = document.getElementById('btn-copilot-send');
    
    const sendQuery = async (queryText) => {
        if (!queryText) return;
        
        appendMessage(queryText, 'outgoing');
        chatInput.value = '';
        
        try {
            const response = await fetch('/api/copilot/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: "demo_user",
                    query: queryText,
                    context: { title: "Software Engineer", location: "San Francisco", current_salary: 130000 }
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                document.getElementById('current-agent-label').textContent = data.agent || "Coordinator";
                appendMessage(data.response, 'incoming', data.agent);
                
                // If TTS is enabled, speak response
                if (!document.getElementById('voice-overlay').classList.contains('hidden')) {
                    speakText(data.response);
                }
            }
        } catch (e) {
            console.warn("Backend API unavailable, using mock agent response.");
            setTimeout(() => {
                const agent = queryText.toLowerCase().includes('salary') ? "Salary Agent" : "Career Coach";
                document.getElementById('current-agent-label').textContent = agent;
                appendMessage(`Mock ${agent}: I've analyzed your request regarding '${queryText}'.`, 'incoming', agent);
            }, 1000);
        }
    };
    
    sendBtn.addEventListener('click', () => sendQuery(chatInput.value.trim()));
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendQuery(chatInput.value.trim());
    });

    function appendMessage(text, type, agentName = null) {
        const container = document.getElementById('copilot-chat');
        const msg = document.createElement('div');
        msg.className = `msg-bubble ${type}`;
        
        if (type === 'incoming' && agentName) {
            msg.innerHTML = `<strong>${agentName}:</strong> ${text}`;
        } else {
            msg.textContent = text;
        }
        
        container.appendChild(msg);
        container.scrollTop = container.scrollHeight;
    }

    // --- Voice Logic (Web Speech API) ---
    const voiceTrigger = document.getElementById('btn-voice-trigger');
    const voiceOverlay = document.getElementById('voice-overlay');
    const voiceClose = document.getElementById('btn-voice-close');
    const voiceTranscript = document.getElementById('voice-transcript');
    
    let recognition;
    
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRec();
        recognition.continuous = false;
        recognition.interimResults = true;
        
        recognition.onstart = () => {
            voiceOverlay.classList.remove('hidden');
            voiceTranscript.textContent = "Listening...";
        };
        
        recognition.onresult = (event) => {
            let interimTranscript = '';
            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    const finalTranscript = event.results[i][0].transcript;
                    voiceTranscript.textContent = `"${finalTranscript}"`;
                    // Send to AI Agent
                    sendQuery(finalTranscript);
                    setTimeout(() => closeVoice(), 2000);
                } else {
                    interimTranscript += event.results[i][0].transcript;
                    voiceTranscript.textContent = `"${interimTranscript}"`;
                }
            }
        };
        
        recognition.onerror = (event) => {
            voiceTranscript.textContent = `Error: ${event.error}`;
            setTimeout(() => closeVoice(), 2000);
        };
        
        recognition.onend = () => {
            // Check if we should close or keep open
        };
    } else {
        console.warn("Web Speech API not supported in this browser.");
    }

    voiceTrigger.addEventListener('click', () => {
        if (recognition) {
            try { recognition.start(); } catch(e) {}
        } else {
            alert("Speech Recognition not supported in this browser.");
        }
    });
    
    function closeVoice() {
        voiceOverlay.classList.add('hidden');
        if (recognition) recognition.stop();
        window.speechSynthesis.cancel();
    }
    
    voiceClose.addEventListener('click', closeVoice);

    // --- TTS (Text to Speech) ---
    function speakText(text) {
        if ('speechSynthesis' in window) {
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.rate = 1.0;
            window.speechSynthesis.speak(utterance);
        }
    }
});
