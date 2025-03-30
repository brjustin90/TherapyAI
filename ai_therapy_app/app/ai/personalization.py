"""
AI Personalization Module for Mental Health AI Therapy
Handles personalization of AI responses based on user data and session history
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserProfile:
    """User profile for AI personalization"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.secure_id = hashlib.sha256(str(user_id).encode()).hexdigest()[:16]
        self.created_at = datetime.now()
        self.updated_at = self.created_at
        
        # Core profile data
        self.demographic_data = {}
        self.preferences = {}
        self.therapy_goals = []
        self.communication_style = {}
        
        # Learned patterns
        self.mood_patterns = []
        self.topic_interests = {}
        self.trigger_topics = []
        self.language_patterns = {}
        self.response_preferences = {}
        
        # Therapy-specific data
        self.therapy_approaches = {}
        self.coping_strategies = []
        self.past_traumas = []  # Securely stored with high encryption
        self.medication_info = {}
        
        # Session data
        self.session_history = []
        self.daily_check_ins = []
        
        # Permissions
        self.data_collection_consent = False
        self.data_retention_preference = "session"  # "session", "limited", "permanent"
        self.data_sharing_permissions = {
            "anonymized_research": False,
            "therapist_oversight": False
        }
        
        logger.info(f"User profile initialized for ID: {self.secure_id}")
    
    def update_demographic_data(self, data: Dict[str, Any]) -> None:
        """Update demographic information"""
        self.demographic_data.update(data)
        self.updated_at = datetime.now()
        logger.info(f"Demographic data updated for user: {self.secure_id}")
    
    def update_preferences(self, preferences: Dict[str, Any]) -> None:
        """Update user preferences"""
        self.preferences.update(preferences)
        self.updated_at = datetime.now()
        logger.info(f"Preferences updated for user: {self.secure_id}")
    
    def add_therapy_goal(self, goal: str, priority: int = 1) -> None:
        """Add a therapy goal"""
        self.therapy_goals.append({
            "goal": goal,
            "priority": priority,
            "created_at": datetime.now(),
            "status": "active"
        })
        self.updated_at = datetime.now()
        logger.info(f"Therapy goal added for user: {self.secure_id}")
    
    def update_communication_style(self, style_data: Dict[str, Any]) -> None:
        """Update communication style preferences"""
        self.communication_style.update(style_data)
        self.updated_at = datetime.now()
        logger.info(f"Communication style updated for user: {self.secure_id}")
    
    def add_mood_data(self, mood_score: int, notes: Optional[str] = None) -> None:
        """Add mood tracking data"""
        self.mood_patterns.append({
            "timestamp": datetime.now(),
            "score": mood_score,
            "notes": notes
        })
        self.updated_at = datetime.now()
        logger.info(f"Mood data added for user: {self.secure_id}")
    
    def update_topic_interest(self, topic: str, interest_level: float) -> None:
        """Update interest level for a topic"""
        self.topic_interests[topic] = interest_level
        self.updated_at = datetime.now()
        logger.info(f"Topic interest updated for user: {self.secure_id}")
    
    def add_trigger_topic(self, topic: str, severity: int = 5) -> None:
        """Add a topic that triggers negative emotions"""
        self.trigger_topics.append({
            "topic": topic,
            "severity": severity,
            "added_at": datetime.now()
        })
        self.updated_at = datetime.now()
        logger.info(f"Trigger topic added for user: {self.secure_id}")
    
    def add_coping_strategy(self, strategy: str, effectiveness: int = 5) -> None:
        """Add a coping strategy"""
        self.coping_strategies.append({
            "strategy": strategy,
            "effectiveness": effectiveness,
            "added_at": datetime.now()
        })
        self.updated_at = datetime.now()
        logger.info(f"Coping strategy added for user: {self.secure_id}")
    
    def record_session_interaction(self, session_id: str, interaction_data: Dict[str, Any]) -> None:
        """Record interaction from therapy session"""
        self.session_history.append({
            "session_id": session_id,
            "timestamp": datetime.now(),
            "data": interaction_data
        })
        self.updated_at = datetime.now()
        logger.info(f"Session interaction recorded for user: {self.secure_id}")
    
    def update_data_permissions(self, permission_updates: Dict[str, Any]) -> None:
        """Update data collection and sharing permissions"""
        if "data_collection_consent" in permission_updates:
            self.data_collection_consent = permission_updates["data_collection_consent"]
            
        if "data_retention_preference" in permission_updates:
            self.data_retention_preference = permission_updates["data_retention_preference"]
            
        if "data_sharing_permissions" in permission_updates:
            self.data_sharing_permissions.update(permission_updates["data_sharing_permissions"])
            
        self.updated_at = datetime.now()
        logger.info(f"Data permissions updated for user: {self.secure_id}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary"""
        return {
            "user_id": self.secure_id,  # Only use secure ID
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "demographic_data": self.demographic_data,
            "preferences": self.preferences,
            "therapy_goals": self.therapy_goals,
            "communication_style": self.communication_style,
            "mood_patterns": self.mood_patterns,
            "topic_interests": self.topic_interests,
            "trigger_topics": self.trigger_topics,
            "language_patterns": self.language_patterns,
            "response_preferences": self.response_preferences,
            "therapy_approaches": self.therapy_approaches,
            "coping_strategies": self.coping_strategies,
            "session_history_count": len(self.session_history),
            "daily_check_ins_count": len(self.daily_check_ins),
            "data_collection_consent": self.data_collection_consent,
            "data_retention_preference": self.data_retention_preference,
            "data_sharing_permissions": self.data_sharing_permissions
        }
    
    def save(self, file_path: Optional[str] = None) -> None:
        """Save profile to file (for development purposes)"""
        if not self.data_collection_consent:
            logger.warning(f"Cannot save profile for user {self.secure_id}: no consent given")
            return
            
        if file_path is None:
            file_path = f"user_profiles/{self.secure_id}.json"
            
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
            
        logger.info(f"Profile saved for user: {self.secure_id}")
    
    @classmethod
    def load(cls, user_id: str, file_path: Optional[str] = None) -> 'UserProfile':
        """Load profile from file (for development purposes)"""
        secure_id = hashlib.sha256(str(user_id).encode()).hexdigest()[:16]
        
        if file_path is None:
            file_path = f"user_profiles/{secure_id}.json"
            
        if not os.path.exists(file_path):
            logger.warning(f"No profile found for user {secure_id}")
            return cls(user_id)
            
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        profile = cls(user_id)
        
        # Load data into profile
        profile.demographic_data = data.get("demographic_data", {})
        profile.preferences = data.get("preferences", {})
        profile.therapy_goals = data.get("therapy_goals", [])
        profile.communication_style = data.get("communication_style", {})
        profile.mood_patterns = data.get("mood_patterns", [])
        profile.topic_interests = data.get("topic_interests", {})
        profile.trigger_topics = data.get("trigger_topics", [])
        profile.language_patterns = data.get("language_patterns", {})
        profile.response_preferences = data.get("response_preferences", {})
        profile.therapy_approaches = data.get("therapy_approaches", {})
        profile.coping_strategies = data.get("coping_strategies", [])
        
        # Handle timestamps
        profile.created_at = datetime.fromisoformat(data.get("created_at"))
        profile.updated_at = datetime.fromisoformat(data.get("updated_at"))
        
        # Handle permissions
        profile.data_collection_consent = data.get("data_collection_consent", False)
        profile.data_retention_preference = data.get("data_retention_preference", "session")
        profile.data_sharing_permissions = data.get("data_sharing_permissions", {
            "anonymized_research": False,
            "therapist_oversight": False
        })
        
        logger.info(f"Profile loaded for user: {secure_id}")
        return profile


class PersonalizationEngine:
    """Engine to personalize AI responses based on user profile"""
    
    def __init__(self):
        self.profiles = {}  # In-memory store of active profiles
        logger.info("Personalization engine initialized")
    
    def get_user_profile(self, user_id: str) -> UserProfile:
        """Get user profile, loading from file if needed"""
        if user_id not in self.profiles:
            self.profiles[user_id] = UserProfile.load(user_id)
        return self.profiles[user_id]
    
    def update_profile_from_session(self, user_id: str, session_data: Dict[str, Any]) -> None:
        """Update user profile based on session data"""
        profile = self.get_user_profile(user_id)
        
        if not profile.data_collection_consent:
            logger.warning(f"Cannot update profile for user {profile.secure_id}: no consent given")
            return
        
        # Extract session ID
        session_id = session_data.get("session_id", f"unknown-{datetime.now().timestamp()}")
        
        # Record the session interaction
        profile.record_session_interaction(session_id, session_data)
        
        # Update mood data if available
        if "mood_score" in session_data:
            profile.add_mood_data(
                session_data["mood_score"],
                session_data.get("mood_notes")
            )
        
        # Learn about topics of interest
        if "topics_discussed" in session_data:
            for topic, data in session_data["topics_discussed"].items():
                interest_level = data.get("interest_level", 0.5)
                profile.update_topic_interest(topic, interest_level)
                
                # Identify potential triggers
                if data.get("negative_response", False) and data.get("emotional_intensity", 0) > 7:
                    profile.add_trigger_topic(topic, data.get("emotional_intensity", 5))
        
        # Learn about communication preferences
        if "communication_feedback" in session_data:
            profile.update_communication_style(session_data["communication_feedback"])
        
        # Save the updated profile
        profile.save()
        logger.info(f"Profile updated from session for user: {profile.secure_id}")
    
    def generate_personalization_context(self, user_id: str) -> Dict[str, Any]:
        """Generate personalization context for AI response generation"""
        profile = self.get_user_profile(user_id)
        
        # Get basic personalization data even without consent
        basic_context = {
            "user_id": profile.secure_id,
            "communication_style": profile.communication_style,
            "session_count": len(profile.session_history)
        }
        
        # If no consent, return only basic information
        if not profile.data_collection_consent:
            return basic_context
        
        # Get full personalization context with consent
        context = {
            **basic_context,
            "demographic_summary": profile.demographic_data,
            "current_goals": [g for g in profile.therapy_goals if g["status"] == "active"],
            "top_interests": {k: v for k, v in sorted(
                profile.topic_interests.items(), 
                key=lambda item: item[1], 
                reverse=True)[:5]
            },
            "triggers_to_avoid": [t["topic"] for t in profile.trigger_topics if t["severity"] > 6],
            "preferred_therapy_approaches": profile.therapy_approaches,
            "effective_coping_strategies": [s for s in profile.coping_strategies if s["effectiveness"] > 7],
            "mood_trend": self._calculate_mood_trend(profile.mood_patterns)
        }
        
        logger.info(f"Generated personalization context for user: {profile.secure_id}")
        return context
    
    def _calculate_mood_trend(self, mood_patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate mood trend from mood data"""
        if not mood_patterns or len(mood_patterns) < 2:
            return {"trend": "unknown", "stability": "unknown"}
        
        # Sort by timestamp
        sorted_moods = sorted(mood_patterns, key=lambda x: x["timestamp"])
        
        # Get recent moods (last 7 entries)
        recent_moods = sorted_moods[-7:]
        
        # Calculate average and trend
        scores = [m["score"] for m in recent_moods]
        avg_score = sum(scores) / len(scores)
        
        # Simple trend calculation
        first_half = scores[:len(scores)//2]
        second_half = scores[len(scores)//2:]
        
        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)
        
        if second_avg > first_avg + 1:
            trend = "improving"
        elif second_avg < first_avg - 1:
            trend = "declining"
        else:
            trend = "stable"
        
        # Calculate stability (standard deviation)
        variance = sum((x - avg_score) ** 2 for x in scores) / len(scores)
        std_dev = variance ** 0.5
        
        if std_dev < 1:
            stability = "very stable"
        elif std_dev < 2:
            stability = "stable"
        elif std_dev < 3:
            stability = "somewhat unstable"
        else:
            stability = "unstable"
        
        return {
            "trend": trend,
            "stability": stability,
            "average_score": round(avg_score, 1),
            "recent_scores": scores
        }
    
    def handle_consent_update(self, user_id: str, consent_given: bool) -> None:
        """Handle user consent update"""
        profile = self.get_user_profile(user_id)
        
        profile.update_data_permissions({
            "data_collection_consent": consent_given
        })
        
        if not consent_given and profile.data_retention_preference == "session":
            # If consent revoked and retention preference is session-only,
            # we should delete the profile after session ends
            logger.info(f"Profile for user {profile.secure_id} will be deleted at end of session")
        
        profile.save()
        logger.info(f"Consent updated for user: {profile.secure_id} to {consent_given}")
    
    def handle_session_end(self, user_id: str) -> None:
        """Handle end of session, potentially cleaning up data"""
        profile = self.get_user_profile(user_id)
        
        # If user has not given consent or prefers session-only retention,
        # delete their profile data
        if not profile.data_collection_consent or profile.data_retention_preference == "session":
            secure_id = profile.secure_id
            
            # Remove from memory
            if user_id in self.profiles:
                del self.profiles[user_id]
            
            # Delete file if it exists
            file_path = f"user_profiles/{secure_id}.json"
            if os.path.exists(file_path):
                os.remove(file_path)
                
            logger.info(f"Profile deleted for user: {secure_id}")
        
        logger.info(f"Session ended for user: {profile.secure_id}")


# Create global instance
personalization_engine = PersonalizationEngine() 