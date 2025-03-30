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

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    
    Args:
        user_message (str): The user's message
        session_id (str): Unique identifier for the therapy session
        user_id (str, optional): Identifier for the user
        personalization_context (dict, optional): Additional context for personalization
        
    Returns:
        str: The AI therapist's response
    """
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
            return generate_demo_response(user_message, personalization_context)
        
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
        
        return ai_response
        
    except Exception as e:
        logger.error(f"Error getting LLM response: {str(e)}")
        return "I'm having trouble connecting with my thoughts right now. Could you give me a moment, and perhaps rephrase what you were saying? I want to be fully present for our conversation."


def generate_demo_response(user_message, personalization_context=None):
    """
    Generate a more sophisticated demo response when no API key is available.
    Uses simple NLP techniques to create more contextual responses.
    """
    user_message = user_message.lower()
    
    # Extract potential topics/themes from the message
    topics = []
    if "anxious" in user_message or "anxiety" in user_message or "worried" in user_message:
        topics.append("anxiety")
    if "sad" in user_message or "depressed" in user_message or "unhappy" in user_message:
        topics.append("depression")
    if "relationship" in user_message or "partner" in user_message or "marriage" in user_message:
        topics.append("relationships")
    if "work" in user_message or "job" in user_message or "career" in user_message:
        topics.append("work stress")
    if "family" in user_message or "parent" in user_message or "child" in user_message:
        topics.append("family issues")
    if "sleep" in user_message or "tired" in user_message or "insomnia" in user_message:
        topics.append("sleep problems")
    
    # Default topic if none detected
    if not topics:
        topics.append("general wellbeing")
    
    # Select appropriate response templates based on message content
    if any(word in user_message for word in ["hello", "hi", "hey", "start"]):
        return "Hello! I'm here to support you today. How are you feeling right now? What's been on your mind lately?"
    
    if "?" in user_message:
        return f"That's a thoughtful question about {topics[0]}. I think it's important to explore this further. What specific aspects of this have been most challenging for you?"
    
    if any(word in user_message for word in ["thank", "thanks"]):
        return "You're very welcome. I'm here to support you. Is there anything else on your mind that you'd like to discuss today?"
    
    if any(word in user_message for word in ["bad", "terrible", "awful", "worst"]):
        return f"I'm sorry to hear you're going through such a difficult time with {topics[0]}. That sounds really challenging. Could you tell me more about how this is affecting you day to day?"
    
    if any(word in user_message for word in ["good", "great", "happy", "better"]):
        return f"I'm glad to hear there are some positive aspects to your experience with {topics[0]}. What do you think has contributed to these positive feelings?"
    
    if len(user_message) < 20:
        return f"I notice your response was brief. Could you tell me more about your experience with {topics[0]}? I'm here to listen and understand what you're going through."
    
    # Default responses based on detected topics
    if "anxiety" in topics:
        return "I can hear that anxiety is playing a significant role in your experience. When you feel this anxiety, where do you notice it in your body? And have you found any strategies that help you manage these feelings, even if just temporarily?"
    
    if "depression" in topics:
        return "It sounds like you've been experiencing some difficult emotions lately. Depression can make everything feel more challenging. What small activities have you found that give you even momentary relief or connection?"
    
    if "relationships" in topics:
        return "Relationships can be both deeply fulfilling and challenging. I'm hearing that this particular relationship has been on your mind. What aspects of this relationship are most important to you? And what changes would you like to see?"
    
    if "work stress" in topics:
        return "Work-related stress can have a significant impact on our overall wellbeing. What aspects of your work situation feel most overwhelming right now? And are there any small boundaries you could set to create more space for yourself?"
    
    # General therapeutic response
    return f"Thank you for sharing that with me. I'm hearing that {topics[0]} has been significant for you lately. Could you tell me more about how this has been affecting you emotionally? What feelings come up when you think about this?"


def clear_session_history(session_id):
    """Clear conversation history for a specific session"""
    if session_id in message_history:
        del message_history[session_id]
        return True
    return False 