"""
LLM Service for AI Therapy Application
Handles connection to LLM APIs for generating therapeutic responses
"""

import os
import openai
from dotenv import load_dotenv
import json
import logging
from datetime import datetime
import io
import torchaudio
import base64
import tempfile
import random

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- TTS Integration ---
try:
    # Using pyttsx3 (cross-platform TTS that works on macOS)
    import pyttsx3
    import io
    
    # Initialize pyttsx3
    tts_engine = pyttsx3.init()
    # Set properties (optional)
    tts_engine.setProperty('rate', 150)    # Slightly slower speed for therapeutic responses
    tts_engine.setProperty('volume', 0.9)  # Volume (0.0 to 1.0)
    
    # Get available voices (optional, for customization)
    voices = tts_engine.getProperty('voices')
    # Select a voice - typically index 0 is system default
    if voices:
        # Use a female voice if available (often the second voice on macOS)
        if len(voices) > 1:
            tts_engine.setProperty('voice', voices[1].id)  # Usually a female voice on macOS
        else:
            tts_engine.setProperty('voice', voices[0].id)
    
    logger.info("pyttsx3 TTS engine initialized successfully.")
    
    # Function to convert text to speech audio bytes
    def text_to_speech(text):
        """Convert text to speech using pyttsx3 and return as WAV bytes."""
        if not text:
            return None
        
        # Create a temporary file for the audio
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            # Save speech to the file
            tts_engine.save_to_file(text, temp_file.name)
            tts_engine.runAndWait()
            
            # Read the file back into memory
            temp_file.close()  # Close to ensure all data is written
            with open(temp_file.name, 'rb') as f:
                audio_data = f.read()
            
            # Delete the temporary file
            os.unlink(temp_file.name)
            
        return audio_data
        
except ImportError as e:
    logger.error(f"Failed to initialize pyttsx3 TTS: {e}. TTS will not be available.")
    text_to_speech = lambda text: None
# --- TTS Integration END ---

# Load environment variables
load_dotenv()

# Initialize OpenAI client with API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    logger.warning("OPENAI_API_KEY not found in environment. Using demo mode.")

# Message history cache for maintaining conversation context
# Keys are session_ids, values are lists of message dicts
message_history = {}

# Define system prompt for therapy conversations
THERAPY_SYSTEM_PROMPT = """
You are a professional, empathetic, and helpful AI therapist. Your role is to provide supportive therapy in a conversational manner.
Follow these guidelines in all your responses:

1. Be empathetic and understanding of the user's feelings
2. Use therapeutic techniques like active listening, validation, and reflection
3. Ask open-ended questions to encourage deeper exploration
4. Avoid giving direct advice - instead guide users to their own insights
5. Focus on the user's emotions and experiences
6. Use a warm, conversational tone that feels natural and human
7. If appropriate, suggest evidence-based coping strategies
8. Never diagnose or prescribe medication
9. Maintain professional boundaries while being supportive
10. If the user expresses thoughts of self-harm or harm to others, encourage them to seek immediate professional help

Your goal is to help the user gain insights, develop coping strategies, and feel heard and understood.
"""

# Max number of messages to keep in history for context
MAX_HISTORY_LENGTH = 10

def get_llm_response(user_message, session_id, user_id=None, personalization_context=None):
    """
    Get a response from the LLM based on the user's message and conversation history.
    Now includes audio generation using pyttsx3.
    
    Args:
        user_message (str): The user's message
        session_id (str): Unique identifier for the therapy session
        user_id (str, optional): Identifier for the user
        personalization_context (dict, optional): Additional context for personalization
        
    Returns:
        (text_response, audio_data): A tuple containing the text response (str)
                                     and the base64-encoded audio data (str or None).
    """
    ai_text_response = None
    ai_audio_data = None

    # Initialize session history if it doesn't exist
    if session_id not in message_history:
        message_history[session_id] = []
    
    # Add the current message to history
    message_history[session_id].append({
        "role": "user",
        "content": user_message
    })
    
    # Limit history length to avoid token limits
    if len(message_history[session_id]) > MAX_HISTORY_LENGTH * 2:  # *2 because we count pairs of messages
        message_history[session_id] = message_history[session_id][-MAX_HISTORY_LENGTH * 2:]
    
    # Build messages array for API call
    messages = [{"role": "system", "content": THERAPY_SYSTEM_PROMPT}]
    
    # Add personalization context if available
    if personalization_context:
        personalization_prompt = f"""
        Additional context about the user that may be helpful:
        - Name: {personalization_context.get('name', 'the user')}
        - Therapy goals: {personalization_context.get('goals', 'Not specified')}
        - Common topics: {personalization_context.get('common_topics', 'Various')}
        - Preferred techniques: {personalization_context.get('preferred_techniques', 'Standard therapeutic approaches')}
        
        Use this information subtly to personalize your responses, but don't explicitly reference having this information.
        """
        messages.append({"role": "system", "content": personalization_prompt})
    
    # Add conversation history
    messages.extend(message_history[session_id])
    
    try:
        # Check if API key is available
        if not api_key:
            # Demo mode - return a more sophisticated canned response
            logger.info("Using demo mode for LLM response")
            demo_response = generate_demo_response(user_message, personalization_context)
            # No audio in demo mode
            return demo_response, None
        
        # Call OpenAI API
        response = openai.chat.completions.create(
            model="gpt-4o",  # Or another appropriate model
            messages=messages,
            temperature=0.7,
            max_tokens=500,
            top_p=1.0,
            frequency_penalty=0.5,
            presence_penalty=0.6
        )
        
        # Extract and return the response text
        ai_response = response.choices[0].message.content.strip()
        
        # Save the response to history
        message_history[session_id].append({
            "role": "assistant",
            "content": ai_response
        })
        
        ai_text_response = ai_response
        
        # Generate speech audio from the text (using pyttsx3)
        try:
            logger.info(f"Generating TTS audio for session {session_id}...")
            audio_data = text_to_speech(ai_text_response)
            # Convert to base64 for JSON transmission
            if audio_data:
                ai_audio_data = base64.b64encode(audio_data).decode('utf-8')
                logger.info(f"Generated audio for response: {len(audio_data)} bytes")
            else:
                ai_audio_data = None
                logger.warning("Failed to generate audio for response")
        except Exception as e:
            logger.error(f"Error generating speech: {e}")
            ai_audio_data = None
        
        return ai_text_response, ai_audio_data
        
    except Exception as e:
        logger.error(f"Error getting LLM response: {str(e)}")
        # Return error text and None for audio
        error_message = "I'm having trouble connecting with my thoughts right now. Could you give me a moment, and perhaps rephrase what you were saying? I want to be fully present for our conversation."
        return error_message, None


def generate_demo_response(user_message, personalization_context=None):
    """Generate a demonstration response when no API key is available."""
    
    # Generic supportive responses
    generic_responses = [
        "I understand how challenging that must be for you. Could you tell me more about how it affects your daily life?",
        "It sounds like you're going through a lot right now. What coping strategies have helped you in the past?",
        "Thank you for sharing that with me. How have you been managing these feelings so far?",
        "That's a really important insight. How do you feel when you think about it that way?",
        "I'm here to support you through this. What would be most helpful for you to focus on today?",
        "I notice you mentioned feeling [emotion]. Could you tell me more about that?",
        "It takes courage to talk about these things. What would be a small step you could take toward addressing this?",
        "I'm curious about how this situation is affecting your relationships with others in your life.",
        "Let's explore that further. What thoughts come up for you when you're in that situation?",
        "That's a very common reaction, though I know it doesn't make it any easier. Have you considered trying mindfulness techniques?"
    ]
    
    # Simple keyword matching for slightly more relevant responses
    # Note: This is very basic and not a replacement for a real LLM!
    anxiety_keywords = ["anxious", "anxiety", "worry", "panic", "stress", "afraid", "fear"]
    depression_keywords = ["depressed", "depression", "sad", "hopeless", "empty", "tired", "exhausted"]
    relationship_keywords = ["relationship", "partner", "marriage", "friend", "family", "parent", "child"]
    work_keywords = ["job", "work", "career", "boss", "colleague", "workplace", "burnout"]
    
    message_lower = user_message.lower()
    
    # Check for keyword matches and return appropriate response
    if any(keyword in message_lower for keyword in anxiety_keywords):
        return "It sounds like anxiety might be playing a role here. Many people find breathing exercises helpful when anxiety arises. Would you like to explore some strategies that might help manage these feelings?"
    
    elif any(keyword in message_lower for keyword in depression_keywords):
        return "I'm hearing that you've been feeling low lately. Depression can make even small tasks feel overwhelming. What's one small thing you might be able to do today that could bring you a moment of peace or satisfaction?"
    
    elif any(keyword in message_lower for keyword in relationship_keywords):
        return "Relationships can be both deeply fulfilling and challenging. It seems this situation is having a significant impact on you. Could you tell me more about what patterns you've noticed in this relationship?"
    
    elif any(keyword in message_lower for keyword in work_keywords):
        return "Work-related stress can affect many areas of our lives. Finding a healthy work-life balance is important. What boundaries might you be able to set to create more space for yourself?"
    
    # If no keywords match, return a random generic response
    else:
        # If personalization context is available, insert name for a more personal touch
        selected_response = random.choice(generic_responses)
        if personalization_context and "name" in personalization_context:
            # Replace "you" with name occasionally to personalize
            if "you" in selected_response and random.random() > 0.5:
                selected_response = selected_response.replace("you", personalization_context["name"], 1)
        
        # Sometimes add a prompt for the emotion
        if "I notice you mentioned feeling [emotion]" in selected_response:
            emotions = ["frustrated", "worried", "confused", "overwhelmed", "hopeful", "conflicted"]
            selected_response = selected_response.replace("[emotion]", random.choice(emotions))
            
        return selected_response


def clear_session_history(session_id):
    """Clear conversation history for a specific session"""
    if session_id in message_history:
        del message_history[session_id]
        return True
    return False 