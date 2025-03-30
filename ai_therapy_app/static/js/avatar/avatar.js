/**
 * AI Avatar System for Mental Health AI Therapy
 * Handles 3D avatar rendering, animation, and interaction
 */

class TherapyAvatar {
    constructor(container, options = {}) {
        this.container = container;
        this.options = Object.assign({
            modelPath: '/static/models/avatar/', // Default 3D model path
            emotionSensitivity: 0.7,             // How responsive avatar is to detected emotions
            voicePitch: 1.0,                     // Voice pitch modifier
            avatarType: 'professional',          // Default avatar appearance
            backgroundColor: '#f0f8ff'           // Background color
        }, options);
        
        this.isInitialized = false;
        this.isAnimating = false;
        this.currentEmotion = 'neutral';
        this.emotions = ['neutral', 'happy', 'sad', 'surprised', 'concerned', 'thoughtful'];
        this.blendShapes = {};
        this.audioContext = null;
        this.videoStream = null;
        
        // Emotion detection confidence scores
        this.emotionScores = {
            neutral: 1.0,
            happy: 0.0,
            sad: 0.0,
            surprised: 0.0,
            concerned: 0.0,
            thoughtful: 0.0
        };
        
        // Animation parameters
        this.animationParams = {
            blinkRate: 0.1,
            blinkDuration: 150,
            breathingRate: 0.05,
            breathingDepth: 0.01,
            fidgetRate: 0.03,
            talkingAmplitude: 0.3
        };
        
        // Bind methods
        this.speak = this.speak.bind(this);
        this.animate = this.animate.bind(this);
        this.updateEmotion = this.updateEmotion.bind(this);
        this.onUserEmotion = this.onUserEmotion.bind(this);
    }
    
    /**
     * Initialize the avatar system
     * @returns {Promise} Resolves when avatar is ready
     */
    async initialize() {
        try {
            if (this.isInitialized) return Promise.resolve();
            
            console.log('Initializing AI Avatar...');
            
            // Create canvas element
            this.canvas = document.createElement('canvas');
            this.canvas.width = this.container.clientWidth;
            this.canvas.height = this.container.clientHeight;
            this.canvas.className = 'avatar-canvas';
            this.container.appendChild(this.canvas);
            
            // Create loading indicator
            const loadingElement = document.createElement('div');
            loadingElement.className = 'avatar-loading';
            loadingElement.innerHTML = `
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading avatar...</span>
                </div>
                <p class="mt-2">Loading AI Therapist...</p>
            `;
            this.container.appendChild(loadingElement);
            
            // Initialize Three.js components (simulated)
            await this._initThreeJS();
            
            // Initialize audio context for voice
            await this._initAudio();
            
            // Load the 3D model (simulated)
            await this._loadAvatarModel();
            
            // Remove loading indicator
            this.container.removeChild(loadingElement);
            
            // Start animation loop
            this.isInitialized = true;
            this.animate();
            
            console.log('AI Avatar initialized successfully');
            return Promise.resolve();
        } catch (error) {
            console.error('Error initializing avatar:', error);
            return Promise.reject(error);
        }
    }
    
    /**
     * Make the avatar speak with appropriate animations
     * @param {string} text - The text to speak
     * @param {object} options - Speaking options
     * @returns {Promise} Resolves when speaking is complete
     */
    speak(text, options = {}) {
        if (!this.isInitialized) {
            console.error('Avatar not initialized');
            return Promise.reject(new Error('Avatar not initialized'));
        }
        
        options = Object.assign({
            emotion: this.currentEmotion,
            rate: 1.0,
            pitch: this.options.voicePitch,
            volume: 1.0
        }, options);
        
        return new Promise((resolve) => {
            console.log(`Avatar speaking: "${text}" with emotion: ${options.emotion}`);
            
            // Set emotion based on text content
            this.updateEmotion(options.emotion);
            
            // Simulate speaking timing (avg reading speed ~200 words per minute)
            const wordCount = text.split(' ').length;
            const speakingDuration = (wordCount / 200) * 60 * 1000; // in ms
            
            // Set speaking state
            this.isSpeaking = true;
            
            // Create viseme timeline (lip sync)
            this._createVisemeTimeline(text);
            
            // Use browser's speech synthesis if available
            if ('speechSynthesis' in window) {
                const speech = new SpeechSynthesisUtterance(text);
                speech.rate = options.rate;
                speech.pitch = options.pitch;
                speech.volume = options.volume;
                
                speech.onend = () => {
                    this.isSpeaking = false;
                    resolve();
                };
                
                window.speechSynthesis.speak(speech);
            } else {
                // Fallback if speech synthesis is not available
                setTimeout(() => {
                    this.isSpeaking = false;
                    resolve();
                }, speakingDuration);
            }
        });
    }
    
    /**
     * Update the avatar's emotional state
     * @param {string} emotion - The emotion to express
     * @param {number} intensity - Intensity of the emotion (0-1)
     */
    updateEmotion(emotion, intensity = 1.0) {
        if (!this.emotions.includes(emotion)) {
            console.warn(`Unknown emotion: ${emotion}, defaulting to neutral`);
            emotion = 'neutral';
        }
        
        this.currentEmotion = emotion;
        
        // Reset all emotion scores
        Object.keys(this.emotionScores).forEach(key => {
            this.emotionScores[key] = 0.0;
        });
        
        // Set the current emotion score
        this.emotionScores[emotion] = Math.min(1.0, Math.max(0.0, intensity));
        
        console.log(`Avatar emotion updated to ${emotion} with intensity ${intensity}`);
    }
    
    /**
     * Process user's detected emotion to build rapport
     * @param {string} userEmotion - Detected emotion of the user
     * @param {number} confidence - Confidence score of the detection (0-1)
     */
    onUserEmotion(userEmotion, confidence = 0.7) {
        // If user shows strong negative emotion, show concern
        if ((userEmotion === 'sad' || userEmotion === 'angry' || userEmotion === 'fearful') && 
            confidence > 0.6) {
            this.updateEmotion('concerned', confidence * this.options.emotionSensitivity);
            return;
        }
        
        // Mirror positive emotions to build rapport
        if (userEmotion === 'happy' && confidence > 0.5) {
            this.updateEmotion('happy', confidence * this.options.emotionSensitivity);
            return;
        }
        
        // Show thoughtful expression when user seems confused
        if (userEmotion === 'confused' && confidence > 0.5) {
            this.updateEmotion('thoughtful', confidence * this.options.emotionSensitivity);
            return;
        }
        
        // Default to neutral with slight adjustment toward detected emotion
        this.updateEmotion('neutral', 0.8);
    }
    
    /**
     * Start video call with user
     * @param {MediaStream} userStream - User's video stream
     * @returns {MediaStream} Avatar's video stream
     */
    startVideoCall(userStream) {
        if (!this.isInitialized) {
            console.error('Avatar not initialized');
            return null;
        }
        
        console.log('Starting video call with avatar');
        
        // Create a virtual stream from the canvas
        this.videoStream = this.canvas.captureStream(30); // 30fps
        
        // Set up emotion detection from user stream (simplified simulation)
        this._setupEmotionDetection(userStream);
        
        return this.videoStream;
    }
    
    /**
     * End the video call
     */
    endVideoCall() {
        console.log('Ending video call with avatar');
        
        if (this.videoStream) {
            this.videoStream.getTracks().forEach(track => track.stop());
            this.videoStream = null;
        }
        
        // Reset emotions
        this.updateEmotion('neutral');
    }
    
    /**
     * Animation loop for the avatar
     */
    animate() {
        if (!this.isInitialized) return;
        
        this.isAnimating = true;
        
        // Apply current emotion blend shapes
        this._updateBlendShapes();
        
        // Perform natural idle animations (blinking, breathing, etc.)
        this._performIdleAnimations();
        
        // Add subtle random movements for realism
        this._addMicroExpressions();
        
        // Update rendering (simulated)
        this._renderFrame();
        
        // Continue animation loop
        requestAnimationFrame(this.animate);
    }
    
    // Private methods for implementation details
    
    async _initThreeJS() {
        // Simulated Three.js initialization
        console.log('Initializing 3D rendering engine...');
        await new Promise(resolve => setTimeout(resolve, 300));
        return Promise.resolve();
    }
    
    async _initAudio() {
        // Initialize Web Audio API if available
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            console.log('Audio context initialized');
        } catch (e) {
            console.warn('Could not initialize audio context:', e);
        }
        return Promise.resolve();
    }
    
    async _loadAvatarModel() {
        // Simulated 3D model loading
        console.log(`Loading avatar model: ${this.options.avatarType}`);
        await new Promise(resolve => setTimeout(resolve, 1500));
        
        // Initialize blend shapes for facial expressions
        this.blendShapes = {
            browInnerUp: 0,
            browOuterUp: 0,
            browDown: 0,
            eyeOpen: 1,
            eyeSquint: 0,
            eyeLookUp: 0,
            eyeLookDown: 0,
            eyeLookLeft: 0,
            eyeLookRight: 0,
            mouthClose: 0,
            mouthOpen: 0,
            mouthSmile: 0,
            mouthFrown: 0,
            jawOpen: 0,
            cheekPuff: 0,
            noseSneer: 0
        };
        
        return Promise.resolve();
    }
    
    _createVisemeTimeline(text) {
        // Simplified viseme (lip sync) timeline based on text
        // In a real implementation, this would use a phoneme-to-viseme mapper
        console.log('Creating lip sync animation for speech');
    }
    
    _setupEmotionDetection(userStream) {
        // In a real implementation, this would use a face tracking library
        // to detect user emotions from video
        console.log('Setting up emotion detection from user video');
        
        // Simulate occasional emotion detections
        this._emotionDetectionInterval = setInterval(() => {
            const emotions = Object.keys(this.emotionScores);
            const randomEmotion = emotions[Math.floor(Math.random() * emotions.length)];
            const randomConfidence = 0.5 + Math.random() * 0.5; // 0.5-1.0
            
            // Only react sometimes to make it more realistic
            if (Math.random() > 0.7) {
                this.onUserEmotion(randomEmotion, randomConfidence);
            }
        }, 5000); // Check every 5 seconds
    }
    
    _updateBlendShapes() {
        // Update blend shapes based on current emotion
        // In a real implementation, this would adjust the 3D model's face
        
        // Reset blend shapes toward neutral position
        Object.keys(this.blendShapes).forEach(key => {
            // Gradually move toward zero (except for eyeOpen which defaults to 1)
            const defaultValue = (key === 'eyeOpen') ? 1 : 0;
            this.blendShapes[key] += (defaultValue - this.blendShapes[key]) * 0.1;
        });
        
        // Apply current emotion blend shapes
        switch (this.currentEmotion) {
            case 'happy':
                this.blendShapes.mouthSmile = 0.7 * this.emotionScores.happy;
                this.blendShapes.browInnerUp = 0.3 * this.emotionScores.happy;
                this.blendShapes.eyeSquint = 0.3 * this.emotionScores.happy;
                break;
                
            case 'sad':
                this.blendShapes.mouthFrown = 0.6 * this.emotionScores.sad;
                this.blendShapes.browInnerUp = 0.4 * this.emotionScores.sad;
                this.blendShapes.browOuterUp = -0.2 * this.emotionScores.sad;
                break;
                
            case 'surprised':
                this.blendShapes.eyeOpen = 1 + (0.5 * this.emotionScores.surprised);
                this.blendShapes.browInnerUp = 0.7 * this.emotionScores.surprised;
                this.blendShapes.browOuterUp = 0.7 * this.emotionScores.surprised;
                this.blendShapes.jawOpen = 0.3 * this.emotionScores.surprised;
                break;
                
            case 'concerned':
                this.blendShapes.browInnerUp = 0.5 * this.emotionScores.concerned;
                this.blendShapes.browDown = 0.3 * this.emotionScores.concerned;
                this.blendShapes.mouthClose = 0.2 * this.emotionScores.concerned;
                break;
                
            case 'thoughtful':
                this.blendShapes.eyeLookUp = 0.3 * this.emotionScores.thoughtful;
                this.blendShapes.browOuterUp = 0.2 * this.emotionScores.thoughtful;
                this.blendShapes.mouthClose = 0.1 * this.emotionScores.thoughtful;
                break;
        }
        
        // Apply talking animation if speaking
        if (this.isSpeaking) {
            const talkingAmount = Math.sin(Date.now() * 0.01) * this.animationParams.talkingAmplitude;
            this.blendShapes.jawOpen = 0.2 + Math.max(0, talkingAmount);
            this.blendShapes.mouthOpen = 0.3 + Math.max(0, talkingAmount);
        }
    }
    
    _performIdleAnimations() {
        // Blinking
        if (Math.random() < this.animationParams.blinkRate) {
            this._blink();
        }
        
        // Breathing
        const breathCycle = Math.sin(Date.now() * 0.001 * this.animationParams.breathingRate);
        this.blendShapes.jawOpen += breathCycle * 0.01; // Very subtle jaw movement
        
        // Random micro eye movements
        if (Math.random() < this.animationParams.fidgetRate) {
            const lookAmount = 0.05;
            this.blendShapes.eyeLookUp += (Math.random() * 2 - 1) * lookAmount;
            this.blendShapes.eyeLookLeft += (Math.random() * 2 - 1) * lookAmount;
        }
    }
    
    _blink() {
        // Simulate a blink
        this.blendShapes.eyeOpen = 0;
        
        // After a short delay, open eyes again
        setTimeout(() => {
            this.blendShapes.eyeOpen = 1;
        }, this.animationParams.blinkDuration);
    }
    
    _addMicroExpressions() {
        // Add subtle random variations to face to avoid looking too static
        const microAmount = 0.02;
        Object.keys(this.blendShapes).forEach(key => {
            if (Math.random() < 0.05) { // Only occasionally
                this.blendShapes[key] += (Math.random() * 2 - 1) * microAmount;
            }
        });
    }
    
    _renderFrame() {
        // In a real implementation, this would render the 3D model to the canvas
        // For this demo, we'll draw a simplified representation
        
        const ctx = this.canvas.getContext('2d');
        
        // Clear canvas
        ctx.fillStyle = this.options.backgroundColor;
        ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw avatar face representation based on blend shapes
        this._drawAvatarRepresentation(ctx);
    }
    
    _drawAvatarRepresentation(ctx) {
        const width = this.canvas.width;
        const height = this.canvas.height;
        const centerX = width / 2;
        const centerY = height / 2;
        
        // Draw head
        ctx.fillStyle = '#f2d2bd'; // Skin tone
        ctx.beginPath();
        ctx.ellipse(centerX, centerY, width * 0.25, height * 0.3, 0, 0, Math.PI * 2);
        ctx.fill();
        
        // Draw hair
        ctx.fillStyle = '#6b3e2e'; // Hair color
        ctx.beginPath();
        ctx.ellipse(centerX, centerY - height * 0.15, width * 0.26, height * 0.2, 0, Math.PI, 0);
        ctx.fill();
        
        // Eye positions
        const eyeY = centerY - height * 0.05;
        const leftEyeX = centerX - width * 0.1;
        const rightEyeX = centerX + width * 0.1;
        const eyeWidth = width * 0.08 * this.blendShapes.eyeOpen;
        const eyeHeight = height * 0.04 * this.blendShapes.eyeOpen;
        
        // Draw eyes
        ctx.fillStyle = 'white';
        ctx.beginPath();
        ctx.ellipse(
            leftEyeX + width * 0.02 * this.blendShapes.eyeLookLeft, 
            eyeY + height * 0.02 * this.blendShapes.eyeLookDown, 
            eyeWidth, eyeHeight, 0, 0, Math.PI * 2
        );
        ctx.fill();
        
        ctx.beginPath();
        ctx.ellipse(
            rightEyeX + width * 0.02 * this.blendShapes.eyeLookLeft, 
            eyeY + height * 0.02 * this.blendShapes.eyeLookDown, 
            eyeWidth, eyeHeight, 0, 0, Math.PI * 2
        );
        ctx.fill();
        
        // Draw pupils
        ctx.fillStyle = '#1a1a1a';
        ctx.beginPath();
        ctx.ellipse(
            leftEyeX + width * 0.03 * this.blendShapes.eyeLookLeft, 
            eyeY + height * 0.03 * this.blendShapes.eyeLookDown, 
            eyeWidth * 0.4, eyeHeight * 0.5, 0, 0, Math.PI * 2
        );
        ctx.fill();
        
        ctx.beginPath();
        ctx.ellipse(
            rightEyeX + width * 0.03 * this.blendShapes.eyeLookLeft, 
            eyeY + height * 0.03 * this.blendShapes.eyeLookDown, 
            eyeWidth * 0.4, eyeHeight * 0.5, 0, 0, Math.PI * 2
        );
        ctx.fill();
        
        // Draw eyebrows
        const browY = eyeY - height * 0.05;
        ctx.strokeStyle = '#5a3825';
        ctx.lineWidth = height * 0.015;
        
        // Left eyebrow
        ctx.beginPath();
        ctx.moveTo(leftEyeX - eyeWidth, browY - height * 0.02 * this.blendShapes.browOuterUp);
        ctx.quadraticCurveTo(
            leftEyeX, 
            browY - height * 0.04 * this.blendShapes.browInnerUp + height * 0.03 * this.blendShapes.browDown,
            leftEyeX + eyeWidth, 
            browY - height * 0.01 * this.blendShapes.browInnerUp
        );
        ctx.stroke();
        
        // Right eyebrow
        ctx.beginPath();
        ctx.moveTo(rightEyeX - eyeWidth, browY - height * 0.01 * this.blendShapes.browInnerUp);
        ctx.quadraticCurveTo(
            rightEyeX, 
            browY - height * 0.04 * this.blendShapes.browInnerUp + height * 0.03 * this.blendShapes.browDown,
            rightEyeX + eyeWidth, 
            browY - height * 0.02 * this.blendShapes.browOuterUp
        );
        ctx.stroke();
        
        // Draw nose
        ctx.strokeStyle = '#d4a792';
        ctx.lineWidth = height * 0.01;
        const noseY = centerY + height * 0.02;
        ctx.beginPath();
        ctx.moveTo(centerX, eyeY + height * 0.05);
        ctx.lineTo(centerX, noseY);
        ctx.stroke();
        
        ctx.beginPath();
        ctx.moveTo(centerX - width * 0.03, noseY);
        ctx.quadraticCurveTo(
            centerX, noseY + height * 0.02,
            centerX + width * 0.03, noseY
        );
        ctx.stroke();
        
        // Draw mouth
        const mouthY = centerY + height * 0.15;
        const mouthWidth = width * 0.15;
        const mouthHeight = height * (0.02 + 0.08 * this.blendShapes.jawOpen);
        const smileAmount = this.blendShapes.mouthSmile - this.blendShapes.mouthFrown;
        
        ctx.strokeStyle = '#cc6666';
        ctx.lineWidth = height * 0.01;
        ctx.beginPath();
        ctx.moveTo(centerX - mouthWidth, mouthY + height * 0.03 * smileAmount);
        ctx.quadraticCurveTo(
            centerX, 
            mouthY - height * 0.1 * smileAmount + height * 0.1 * this.blendShapes.jawOpen,
            centerX + mouthWidth, 
            mouthY + height * 0.03 * smileAmount
        );
        ctx.stroke();
        
        // If mouth is open, draw inner mouth
        if (this.blendShapes.jawOpen > 0.1) {
            ctx.fillStyle = '#990000';
            ctx.beginPath();
            ctx.ellipse(
                centerX, 
                mouthY + height * 0.02, 
                mouthWidth * 0.7, 
                mouthHeight * 0.8, 
                0, 0, Math.PI * 2
            );
            ctx.fill();
        }
        
        // Draw emotion-specific features based on current emotion
        switch(this.currentEmotion) {
            case 'happy':
                // Slightly rosy cheeks
                ctx.fillStyle = 'rgba(255, 150, 150, 0.3)';
                ctx.beginPath();
                ctx.ellipse(leftEyeX - width * 0.08, mouthY - height * 0.05, width * 0.08, height * 0.06, 0, 0, Math.PI * 2);
                ctx.fill();
                ctx.beginPath();
                ctx.ellipse(rightEyeX + width * 0.08, mouthY - height * 0.05, width * 0.08, height * 0.06, 0, 0, Math.PI * 2);
                ctx.fill();
                break;
                
            case 'concerned':
                // Slight forehead wrinkle
                ctx.strokeStyle = 'rgba(0, 0, 0, 0.1)';
                ctx.lineWidth = height * 0.005;
                ctx.beginPath();
                ctx.moveTo(centerX - width * 0.15, browY - height * 0.08);
                ctx.quadraticCurveTo(
                    centerX, browY - height * 0.1,
                    centerX + width * 0.15, browY - height * 0.08
                );
                ctx.stroke();
                break;
        }
    }
}

// Export the TherapyAvatar class
window.TherapyAvatar = TherapyAvatar; 