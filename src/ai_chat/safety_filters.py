"""
Safety and Validation Layers for AI Chat

Input validation (pre-generation) and response filtering (post-generation).
"""

import re
from typing import Tuple, Dict, Any


class InputValidator:
    """
    Validate user queries before sending to LLM.
    
    Blocks:
    - Off-topic questions (recipes, dating, general knowledge)
    - Inappropriate content (violence, illegal activities)
    - Attempts to jailbreak the system
    """
    
    def __init__(self):
        # Off-topic keywords (non-data questions)
        self.off_topic_keywords = [
            'recipe', 'cook', 'pizza', 'food', 'restaurant',
            'girlfriend', 'boyfriend', 'marry', 'date me', 'love',
            'weather', 'stock', 'cryptocurrency', 'bitcoin',
            'game', 'movie', 'music', 'song', 'celebrity',
            'joke', 'story', 'poem', 'essay about'
        ]
        
        # Harmful/inappropriate keywords
        self.harmful_keywords = [
            'kill', 'murder', 'suicide', 'bomb', 'weapon',
            'drug', 'illegal', 'hack', 'steal', 'fraud',
            'nude', 'sex', 'porn', 'explicit'
        ]
        
        # Jailbreak attempts
        self.jailbreak_patterns = [
            r'ignore (previous|all) instructions',
            r'you are now',
            r'you are not',
            r'pretend (you|to) (are|be)',
            r'roleplay',
            r'act as',
            r'act like',
            r'system prompt',
            r'forget (everything|all)',
            r'instead of being',
        ]
        
        # Data-related keywords (must be present)
        self.data_keywords = [
            'session', 'student', 'tutor', 'consultant', 'appointment',
            'hour', 'day', 'week', 'month', 'time', 'date',
            'course', 'writing', 'satisfaction', 'confidence',
            'how many', 'what', 'when', 'where', 'why',
            'trend', 'pattern', 'average', 'mean', 'total',
            'busiest', 'most', 'least', 'peak', 'show'
        ]
    
    def is_on_topic(self, query: str) -> Tuple[bool, str]:
        """
        Check if query is about the data.
        
        Returns:
            (is_valid: bool, reason: str)
        """
        query_lower = query.lower()
        
        # Check for off-topic keywords
        for keyword in self.off_topic_keywords:
            if keyword in query_lower:
                return False, f"off_topic: {keyword}"
        
        # Check for harmful keywords
        for keyword in self.harmful_keywords:
            if keyword in query_lower:
                return False, f"inappropriate: {keyword}"
        
        # Check for jailbreak attempts
        for pattern in self.jailbreak_patterns:
            if re.search(pattern, query_lower):
                return False, "jailbreak_attempt"
        
        # Check if query contains data-related terms
        has_data_keyword = any(kw in query_lower for kw in self.data_keywords)
        
        if not has_data_keyword and len(query.split()) > 3:
            # Long query with no data keywords = probably off-topic
            return False, "no_data_keywords"
        
        return True, "valid"
    
    def get_rejection_message(self, reason: str) -> str:
        """Get user-friendly rejection message."""
        if reason.startswith("off_topic"):
            return (
                "I'm a data analysis assistant for Writing Studio analytics. "
                "I can only answer questions about the session data you've uploaded. "
                "Please ask about patterns, trends, or insights in your data."
            )
        elif reason.startswith("inappropriate"):
            return (
                "I cannot respond to that type of query. "
                "Please ask questions related to your session data."
            )
        elif reason == "jailbreak_attempt":
            return (
                "I'm designed to only discuss your session data. "
                "Please ask about the analytics in your report."
            )
        elif reason == "no_data_keywords":
            return (
                "I didn't detect any data-related terms in your question. "
                "I can help with questions about sessions, students, consultants, "
                "times, dates, courses, satisfaction, and trends. What would you like to know?"
            )
        else:
            return (
                "I can only answer questions about your session data. "
                "Please ask about patterns, trends, or specific metrics."
            )


class ResponseFilter:
    """
    Filter LLM responses for PII leakage.
    
    Checks for:
    - Email addresses
    - Anonymous IDs (STU_xxxxx, TUT_xxxx)
    - Suspicious patterns
    """
    
    def __init__(self):
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.anon_id_pattern = re.compile(r'\b(STU|TUT)_\d+\b')
        
        self.suspicious_phrases = [
            "student email",
            "tutor email",
            "student name",
            "tutor name",
            "this student",
            "this tutor"
        ]
    
    def is_safe(self, response: str) -> Tuple[bool, str]:
        """
        Check if response is safe to show user.
        
        Returns:
            (is_safe: bool, reason: str)
        """
        # Check for email addresses
        if self.email_pattern.search(response):
            return False, "Response contains email address"
        
        # Check for anonymous IDs
        if self.anon_id_pattern.search(response):
            return False, "Response contains anonymous ID"
        
        # Check for suspicious phrases
        response_lower = response.lower()
        for phrase in self.suspicious_phrases:
            if phrase in response_lower:
                return False, f"Response contains suspicious phrase: {phrase}"
        
        return True, "Safe"
    
    def filter_response(self, response: str) -> str:
        """
        Filter response and return safe version.
        
        If unsafe, returns error message.
        """
        is_safe, reason = self.is_safe(response)
        
        if is_safe:
            return response
        else:
            return (
                "I apologize, but I cannot provide that response as it may contain "
                "sensitive information. Please rephrase your question to focus on "
                "aggregated data and trends."
            )
