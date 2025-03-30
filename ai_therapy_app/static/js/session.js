/**
 * Session management and chat functionality
 * For therapy session interaction
 */

class TherapySession {
    constructor(sessionId) {
        this.sessionId = sessionId;
        this.messageHistory = [];
        this.isInProgress = false;
    }

    async startSession() {
        try {
            this.isInProgress = true;
            const response = await fetch(`/api/v1/sessions/${this.sessionId}/start`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            if (!response.ok) {
                throw new Error('Failed to start session');
            }
            
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error starting session:', error);
            this.isInProgress = false;
            throw error;
        }
    }

    async endSession() {
        try {
            this.isInProgress = false;
            const response = await fetch(`/api/v1/sessions/${this.sessionId}/end`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            if (!response.ok) {
                throw new Error('Failed to end session');
            }
            
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error ending session:', error);
            throw error;
        }
    }

    async sendMessage(message) {
        try {
            const response = await fetch(`/api/v1/sessions/${this.sessionId}/message`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message })
            });
            
            if (!response.ok) {
                throw new Error('Failed to send message');
            }
            
            const data = await response.json();
            this.messageHistory.push({
                content: message,
                isFromAI: false,
                timestamp: new Date()
            });
            
            if (data.response) {
                this.messageHistory.push({
                    content: data.response,
                    isFromAI: true,
                    timestamp: new Date()
                });
            }
            
            return data;
        } catch (error) {
            console.error('Error sending message:', error);
            throw error;
        }
    }

    getMessageHistory() {
        return this.messageHistory;
    }
}

// Initialize session functionality when page loads
document.addEventListener('DOMContentLoaded', function() {
    const sessionContainer = document.getElementById('session-container');
    
    if (sessionContainer) {
        const sessionId = sessionContainer.dataset.sessionId;
        const session = new TherapySession(sessionId);
        
        // Add to window for debugging purposes
        window.therapySession = session;
        
        // Start button
        const startBtn = document.getElementById('start-session-btn');
        if (startBtn) {
            startBtn.addEventListener('click', async function() {
                try {
                    startBtn.disabled = true;
                    startBtn.textContent = 'Starting...';
                    
                    await session.startSession();
                    
                    document.getElementById('session-status').textContent = 'In Progress';
                    document.getElementById('chat-container').classList.remove('d-none');
                    startBtn.classList.add('d-none');
                    document.getElementById('end-session-btn').classList.remove('d-none');
                } catch (error) {
                    startBtn.disabled = false;
                    startBtn.textContent = 'Start Session';
                    alert('Failed to start session. Please try again.');
                }
            });
        }
        
        // End button
        const endBtn = document.getElementById('end-session-btn');
        if (endBtn) {
            endBtn.addEventListener('click', async function() {
                if (confirm('Are you sure you want to end this session?')) {
                    try {
                        endBtn.disabled = true;
                        endBtn.textContent = 'Ending...';
                        
                        await session.endSession();
                        
                        document.getElementById('session-status').textContent = 'Completed';
                        endBtn.classList.add('d-none');
                        document.getElementById('chat-form').classList.add('d-none');
                        document.getElementById('session-completed-message').classList.remove('d-none');
                    } catch (error) {
                        endBtn.disabled = false;
                        endBtn.textContent = 'End Session';
                        alert('Failed to end session. Please try again.');
                    }
                }
            });
        }
        
        // Video button
        const videoBtn = document.getElementById('start-video-btn');
        if (videoBtn) {
            videoBtn.addEventListener('click', function() {
                try {
                    // Redirect to video_session page
                    window.location.href = `/video_session/${sessionId}`;
                } catch (error) {
                    console.error('Error redirecting to video session:', error);
                    alert('Failed to start video session. Please try again.');
                }
            });
        }
    }
}); 