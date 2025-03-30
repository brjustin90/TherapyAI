/**
 * Video Call Interface for Mental Health AI Therapy
 * Handles WebRTC connections between user and AI avatar
 */

export class TherapyVideoCall {
    constructor(options = {}) {
        this.options = Object.assign({
            userVideoElement: null,      // User video element
            avatarContainer: null,       // Container for AI avatar
            controlsContainer: null,     // Container for call controls
            chatContainer: null,         // Container for text chat during call
            sessionId: null,             // Current therapy session ID
            avatarType: 'photorealistic',  // Type of avatar to use (3d or photorealistic)
            autoStartUserMedia: true     // Auto-start user's camera
        }, options);
        
        // State variables
        this.isCallActive = false;
        this.isMicMuted = false;
        this.isCameraOff = false;
        this.userStream = null;
        this.avatar = null;
        this.transcript = [];
        this.recognitionActive = false;
        this.recognition = null;
        this.pendingUserSpeech = '';
        this.isTalking = false;
        
        // Bind methods
        this.startCall = this.startCall.bind(this);
        this.endCall = this.endCall.bind(this);
        this.toggleMic = this.toggleMic.bind(this);
        this.toggleCamera = this.toggleCamera.bind(this);
        this.onUserSpeech = this.onUserSpeech.bind(this);
        this.sendTextMessage = this.sendTextMessage.bind(this);
        this._handleAvatarTalking = this._handleAvatarTalking.bind(this);
    }
    
    /**
     * Initialize the video call interface
     * @returns {Promise} Resolves when interface is ready
     */
    async initialize() {
        console.log('Initializing therapy video call interface...');
        
        // Create UI elements if not provided
        this._setupUI();
        
        // Initialize speech recognition if available
        this._initSpeechRecognition();
        
        // Simple approach for photorealistic avatar - just use the img element
        // that's already in the HTML - no need to create a 3D avatar
        if (this.options.avatarType === 'photorealistic') {
            // We'll just use the static image directly from the HTML
            this.avatarImage = document.getElementById('therapist-avatar-image');
            this.photorealisticAvatar = document.querySelector('.photorealistic-avatar');
            
            if (!this.avatarImage) {
                console.error('Could not find therapist avatar image');
            }
            
            console.log('Using photorealistic avatar');
        } else {
            // For 3D avatar, we would initialize it here
            try {
                // Import the avatar module dynamically
                const TherapyAvatar = window.TherapyAvatar;
                if (!TherapyAvatar) {
                    throw new Error('TherapyAvatar module not found');
                }
                
                this.avatar = new TherapyAvatar(this.options.avatarContainer, {
                    avatarType: 'professional'
                });
                
                await this.avatar.initialize();
            } catch (error) {
                console.error('Error initializing 3D avatar:', error);
                // Fallback to photorealistic
                this.options.avatarType = 'photorealistic';
            }
        }
        
        console.log('Video call interface initialized');
        return Promise.resolve();
    }
    
    /**
     * Start a video call session
     * @returns {Promise} Resolves when call is started
     */
    async startCall() {
        if (this.isCallActive) {
            console.warn('Call is already active');
            return Promise.resolve();
        }
        
        try {
            console.log('Starting video call...');
            
            // Request user media if not already available
            if (!this.userStream) {
                await this._requestUserMedia();
            }
            
            // Start the avatar's video stream if using 3D avatar
            if (this.avatar && this.options.avatarType !== 'photorealistic') {
                const avatarStream = this.avatar.startVideoCall(this.userStream);
            }
            
            // Update UI to show call is active
            this._updateCallUI(true);
            
            // Start speech recognition if available
            this._startSpeechRecognition();
            
            // Initial greeting from avatar
            const initialGreeting = "Hello, I'm your AI therapy assistant. How are you feeling today?";
            
            if (this.options.avatarType === 'photorealistic') {
                // For photorealistic avatar, we just display the message and animate the image
                this._handleAvatarTalking(true);
                await this._addSystemMessage(initialGreeting);
                await new Promise(resolve => setTimeout(resolve, 3000));
                this._handleAvatarTalking(false);
            } else if (this.avatar) {
                // For 3D avatar
                await this.avatar.speak(initialGreeting, {
                    emotion: 'happy',
                    pitch: 1.0,
                    rate: 0.9
                });
            }
            
            this.isCallActive = true;
            console.log('Video call started successfully');
            
            return Promise.resolve();
        } catch (error) {
            console.error('Error starting video call:', error);
            this._showError('Failed to start video call. Please try again.');
            return Promise.reject(error);
        }
    }
    
    /**
     * End the current video call session
     */
    async endCall() {
        if (!this.isCallActive) {
            console.warn('No active call to end');
            return Promise.resolve();
        }
        
        console.log('Ending video call...');
        
        // Stop speech recognition
        this._stopSpeechRecognition();
        
        // Final message from avatar
        const finalMessage = "Thank you for the session today. I hope you found it helpful. Take care and I look forward to our next conversation.";
        
        try {
            if (this.options.avatarType === 'photorealistic') {
                // For photorealistic avatar
                this._handleAvatarTalking(true);
                await this._addSystemMessage(finalMessage);
                await new Promise(resolve => setTimeout(resolve, 3000));
                this._handleAvatarTalking(false);
            } else if (this.avatar) {
                // For 3D avatar
                await this.avatar.speak(finalMessage, {
                    emotion: 'happy',
                    pitch: 1.0,
                    rate: 0.9
                });
            }
        } catch (e) {
            console.warn('Error during final message:', e);
        }
        
        // End avatar video call (for 3D avatar)
        if (this.avatar && this.options.avatarType !== 'photorealistic') {
            this.avatar.endVideoCall();
        }
        
        // Update UI
        this._updateCallUI(false);
        
        // Stop user media
        this._stopUserMedia();
        
        // Save session transcript
        try {
            await this._saveTranscript();
        } catch (e) {
            console.warn('Error saving transcript:', e);
        }
        
        this.isCallActive = false;
        console.log('Video call ended successfully');
        
        return Promise.resolve();
    }
    
    /**
     * Toggle microphone mute state
     */
    toggleMic() {
        if (!this.userStream) return;
        
        const audioTracks = this.userStream.getAudioTracks();
        if (audioTracks.length === 0) return;
        
        this.isMicMuted = !this.isMicMuted;
        
        audioTracks.forEach(track => {
            track.enabled = !this.isMicMuted;
        });
        
        // Update UI
        const micButton = document.getElementById('mic-toggle');
        if (micButton) {
            if (this.isMicMuted) {
                micButton.innerHTML = '<i class="fas fa-microphone-slash"></i>';
                micButton.classList.replace('btn-outline-primary', 'btn-danger');
                this._stopSpeechRecognition();
            } else {
                micButton.innerHTML = '<i class="fas fa-microphone"></i>';
                micButton.classList.replace('btn-danger', 'btn-outline-primary');
                this._startSpeechRecognition();
            }
        }
        
        console.log(`Microphone ${this.isMicMuted ? 'muted' : 'unmuted'}`);
    }
    
    /**
     * Toggle camera on/off state
     */
    toggleCamera() {
        if (!this.userStream) return;
        
        const videoTracks = this.userStream.getVideoTracks();
        if (videoTracks.length === 0) return;
        
        this.isCameraOff = !this.isCameraOff;
        
        videoTracks.forEach(track => {
            track.enabled = !this.isCameraOff;
        });
        
        // Update UI
        const cameraButton = document.getElementById('camera-toggle');
        if (cameraButton) {
            if (this.isCameraOff) {
                cameraButton.innerHTML = '<i class="fas fa-video-slash"></i>';
                cameraButton.classList.replace('btn-outline-primary', 'btn-danger');
            } else {
                cameraButton.innerHTML = '<i class="fas fa-video"></i>';
                cameraButton.classList.replace('btn-danger', 'btn-outline-primary');
            }
        }
        
        // Update video element
        if (this.options.userVideoElement) {
            this.options.userVideoElement.style.display = this.isCameraOff ? 'none' : 'block';
        }
        
        console.log(`Camera ${this.isCameraOff ? 'disabled' : 'enabled'}`);
    }
    
    /**
     * Handle user speech from speech recognition
     * @param {string} text - The recognized speech text
     */
    async onUserSpeech(text) {
        if (!text || !this.isCallActive) return;
        
        console.log('User speech recognized:', text);
        
        // Add user message to chat
        await this._addUserMessage(text);
        
        // Get AI response
        const aiResponse = await this._getAIResponse(text);
        
        // Add to transcript
        this.transcript.push({
            sender: 'user',
            message: text,
            timestamp: new Date().toISOString()
        });
        
        return aiResponse;
    }
    
    /**
     * Send a text message in the chat
     * @param {string} message - Text message to send
     */
    async sendTextMessage(message) {
        if (!message || message.trim() === '') return;
        
        console.log(`Sending text message: "${message}"`);
        
        // Same processing as speech
        await this.onUserSpeech(message);
    }
    
    // Private methods
    
    _setupUI() {
        // Setup only needed UI elements that aren't provided
        if (!this.options.userVideoElement) {
            console.log('Creating user video element');
            this.options.userVideoElement = document.createElement('video');
            this.options.userVideoElement.autoplay = true;
            this.options.userVideoElement.muted = true; // Mute to prevent feedback
            this.options.userVideoElement.classList.add('user-video');
            this.options.avatarContainer.parentNode.appendChild(this.options.userVideoElement);
        }
        
        if (!this.options.controlsContainer) {
            console.log('Creating controls container');
            this.options.controlsContainer = document.createElement('div');
            this.options.controlsContainer.classList.add('video-controls');
            this.options.avatarContainer.parentNode.appendChild(this.options.controlsContainer);
            
            // Add control buttons
            this.options.controlsContainer.innerHTML = `
                <button id="mic-toggle" class="btn btn-outline-primary"><i class="fas fa-microphone"></i></button>
                <button id="camera-toggle" class="btn btn-outline-primary"><i class="fas fa-video"></i></button>
                <button id="end-call" class="btn btn-danger"><i class="fas fa-phone-slash"></i></button>
            `;
            
            // Add event listeners
            document.getElementById('mic-toggle').addEventListener('click', this.toggleMic);
            document.getElementById('camera-toggle').addEventListener('click', this.toggleCamera);
            document.getElementById('end-call').addEventListener('click', this.endCall);
        }
        
        if (!this.options.chatContainer) {
            console.log('Creating chat container');
            this.options.chatContainer = document.createElement('div');
            this.options.chatContainer.classList.add('video-chat');
            this.options.avatarContainer.parentNode.appendChild(this.options.chatContainer);
            
            // Add chat UI
            this.options.chatContainer.innerHTML = `
                <div class="chat-messages"></div>
                <div class="chat-input-container">
                    <input type="text" class="chat-input form-control" placeholder="Type a message...">
                    <button class="btn btn-primary chat-send"><i class="fas fa-paper-plane"></i></button>
                </div>
            `;
            
            // Add event listener for chat
            const chatInput = this.options.chatContainer.querySelector('.chat-input');
            const chatSend = this.options.chatContainer.querySelector('.chat-send');
            
            chatSend.addEventListener('click', () => {
                const message = chatInput.value.trim();
                if (message) {
                    this.sendTextMessage(message);
                    chatInput.value = '';
                }
            });
            
            chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    const message = chatInput.value.trim();
                    if (message) {
                        this.sendTextMessage(message);
                        chatInput.value = '';
                    }
                }
            });
        }
    }
    
    async _requestUserMedia() {
        try {
            console.log('Requesting user media...');
            this.userStream = await navigator.mediaDevices.getUserMedia({
                audio: true,
                video: true
            });
            
            // Set the stream to the video element
            if (this.options.userVideoElement) {
                this.options.userVideoElement.srcObject = this.userStream;
            }
            
            return Promise.resolve(this.userStream);
        } catch (error) {
            console.error('Error accessing user media:', error);
            this._showError(`Media access error: ${error.message}`);
            return Promise.reject(error);
        }
    }
    
    _initSpeechRecognition() {
        // Initialize speech recognition if available
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            console.warn('Speech recognition not supported in this browser');
            return;
        }
        
        const SpeechRecognition = window.webkitSpeechRecognition || window.SpeechRecognition;
        this.recognition = new SpeechRecognition();
        
        this.recognition.continuous = true;
        this.recognition.interimResults = true;
        this.recognition.lang = 'en-US';
        
        this.recognition.onresult = (event) => {
            let interimTranscript = '';
            let finalTranscript = '';
            
            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    finalTranscript += event.results[i][0].transcript;
                } else {
                    interimTranscript += event.results[i][0].transcript;
                }
            }
            
            // Update pending speech
            this.pendingUserSpeech = interimTranscript;
            
            // If we have final transcript, send to AI
            if (finalTranscript) {
                this.pendingUserSpeech = '';
                this.onUserSpeech(finalTranscript);
            }
        };
        
        this.recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            
            // Restart on error
            if (this.recognitionActive) {
                setTimeout(() => {
                    this._startSpeechRecognition();
                }, 1000);
            }
        };
        
        this.recognition.onend = () => {
            console.log('Speech recognition ended');
            
            // Restart if still active
            if (this.recognitionActive) {
                this._startSpeechRecognition();
            }
        };
    }
    
    _startSpeechRecognition() {
        if (!this.recognition || this.recognitionActive || this.isMicMuted) return;
        
        try {
            this.recognition.start();
            this.recognitionActive = true;
            console.log('Speech recognition started');
        } catch (e) {
            console.error('Error starting speech recognition:', e);
        }
    }
    
    _stopSpeechRecognition() {
        if (!this.recognition || !this.recognitionActive) return;
        
        try {
            this.recognition.stop();
            this.recognitionActive = false;
            console.log('Speech recognition stopped');
        } catch (e) {
            console.error('Error stopping speech recognition:', e);
        }
    }
    
    async _getAIResponse(userMessage) {
        // In a real implementation, this would call the backend API
        console.log('Getting AI response for:', userMessage);
        
        try {
            const sessionId = this.options.sessionId || 'temp-session';
            console.log('Making API call to:', `/sessions/${sessionId}/videocall`);
            
            const response = await fetch(`/sessions/${sessionId}/videocall`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    action: 'message',
                    message: userMessage 
                })
            });
            
            console.log('API response status:', response.status);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('API error response:', errorText);
                throw new Error(`API request failed: ${response.status} - ${errorText}`);
            }
            
            const data = await response.json();
            console.log('API response data:', data);
            
            // Show the AI response
            const aiResponse = data.response || 'I apologize, but I had trouble processing your message.';
            
            // If using photorealistic avatar, animate talking
            if (this.options.avatarType === 'photorealistic') {
                this._handleAvatarTalking(true);
                await this._addAIMessage(aiResponse);
                
                // Simulate talking duration based on message length
                const talkingDuration = Math.min(Math.max(aiResponse.length * 50, 1000), 5000);
                await new Promise(resolve => setTimeout(resolve, talkingDuration));
                
                this._handleAvatarTalking(false);
            } else if (this.avatar) {
                // For 3D avatar, use speech synthesis
                await this.avatar.speak(aiResponse, {
                    emotion: 'neutral',
                    pitch: 1.0,
                    rate: 0.9
                });
            }
            
            return aiResponse;
        } catch (error) {
            console.error('Error getting AI response:', error);
            
            // Fallback responses for demo
            const fallbackResponses = [
                "I understand how you're feeling. Could you tell me more about that?",
                "That's interesting. How does that make you feel?",
                "Thank you for sharing that with me. Let's explore that further.",
                "I'm here to listen and help. What else is on your mind?",
                "It sounds like that's been challenging for you. How have you been coping?",
                "I appreciate your openness. What thoughts come up when you consider that situation?"
            ];
            
            const fallbackResponse = fallbackResponses[Math.floor(Math.random() * fallbackResponses.length)];
            
            // Show fallback response with avatar animation
            if (this.options.avatarType === 'photorealistic') {
                this._handleAvatarTalking(true);
                await this._addAIMessage(fallbackResponse);
                await new Promise(resolve => setTimeout(resolve, 3000));
                this._handleAvatarTalking(false);
            }
            
            return fallbackResponse;
        }
    }
    
    _updateCallUI(isActive) {
        // Show/hide UI elements based on call state
        if (this.options.userVideoElement) {
            this.options.userVideoElement.style.display = isActive ? 'block' : 'none';
        }
        
        if (this.options.controlsContainer) {
            this.options.controlsContainer.style.display = isActive ? 'flex' : 'none';
        }
        
        if (this.options.chatContainer) {
            this.options.chatContainer.style.display = isActive ? 'flex' : 'none';
        }
    }
    
    _addMessageToChat(message, sender) {
        if (!this.options.chatContainer) return;
        
        const chatMessages = this.options.chatContainer.querySelector('.chat-messages');
        if (!chatMessages) return;
        
        const messageElement = document.createElement('div');
        messageElement.classList.add('chat-message', `${sender}-message`);
        
        const now = new Date();
        const timeString = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        messageElement.innerHTML = `
            <div class="message-content">${message}</div>
            <div class="message-time">${timeString}</div>
        `;
        
        chatMessages.appendChild(messageElement);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    _addAIMessage(message) {
        if (!this.options.chatContainer) return;
        
        const chatMessages = this.options.chatContainer.querySelector('.chat-messages');
        if (!chatMessages) return;
        
        const messageEl = document.createElement('div');
        messageEl.className = 'ai-message';
        messageEl.innerHTML = `<p>${message}</p><span class="message-time">${new Date().toLocaleTimeString()}</span>`;
        
        chatMessages.appendChild(messageEl);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Add to transcript
        this.transcript.push({
            sender: 'ai',
            message: message,
            timestamp: new Date().toISOString()
        });
        
        return Promise.resolve();
    }
    
    _addSystemMessage(message) {
        if (!this.options.chatContainer) return;
        
        const chatMessages = this.options.chatContainer.querySelector('.chat-messages');
        if (!chatMessages) return;
        
        const messageEl = document.createElement('div');
        messageEl.className = 'system-message';
        messageEl.innerHTML = `<p>${message}</p>`;
        
        chatMessages.appendChild(messageEl);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        return Promise.resolve();
    }
    
    _addUserMessage(message) {
        if (!this.options.chatContainer) return;
        
        const chatMessages = this.options.chatContainer.querySelector('.chat-messages');
        if (!chatMessages) return;
        
        const messageEl = document.createElement('div');
        messageEl.className = 'user-message';
        messageEl.innerHTML = `<p>${message}</p><span class="message-time">${new Date().toLocaleTimeString()}</span>`;
        
        chatMessages.appendChild(messageEl);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Add to transcript
        this.transcript.push({
            sender: 'user',
            message: message,
            timestamp: new Date().toISOString()
        });
        
        return Promise.resolve();
    }
    
    _stopUserMedia() {
        if (this.userStream) {
            this.userStream.getTracks().forEach(track => track.stop());
            this.userStream = null;
        }
    }
    
    async _saveTranscript() {
        if (this.transcript.length === 0) return;
        
        try {
            const sessionId = this.options.sessionId || 'temp-session';
            const response = await fetch(`/sessions/${sessionId}/transcript`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ transcript: this.transcript })
            });
            
            if (!response.ok) {
                throw new Error(`Failed to save transcript: ${response.status}`);
            }
            
            console.log('Session transcript saved successfully');
        } catch (error) {
            console.error('Error saving transcript:', error);
        }
    }
    
    _showError(message) {
        console.error('Video call error:', message);
        
        // Create error toast
        const errorToast = document.createElement('div');
        errorToast.classList.add('error-toast');
        errorToast.innerHTML = `
            <div class="toast-header bg-danger text-white">
                <i class="fas fa-exclamation-circle me-2"></i>
                <strong class="me-auto">Error</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;
        
        document.body.appendChild(errorToast);
        
        // Use Bootstrap toast if available
        if (window.bootstrap && window.bootstrap.Toast) {
            const toast = new window.bootstrap.Toast(errorToast);
            toast.show();
        } else {
            // Simple fallback
            errorToast.style.display = 'block';
            setTimeout(() => {
                errorToast.style.display = 'none';
                document.body.removeChild(errorToast);
            }, 5000);
        }
    }
    
    /**
     * Handle avatar talking animation
     * @param {boolean} isTalking - Whether the avatar is currently talking
     */
    _handleAvatarTalking(isTalking) {
        if (!this.photorealisticAvatar) return;
        
        this.isTalking = isTalking;
        
        if (isTalking) {
            this.photorealisticAvatar.classList.add('talking');
        } else {
            this.photorealisticAvatar.classList.remove('talking');
        }
    }
} 