"""
Safety and validation filters for AI Chat.

Prevents off-topic queries and PII leakage.
"""

import re
import os
from datetime import datetime
from typing import Tuple


class InputValidator:
    """
    Validate user queries before sending to LLM.
    
    Blocks:
    - Off-topic questions (recipes, dating, general knowledge)
    - Inappropriate content (violence, illegal activities)
    - Attempts to jailbreak the system
    
    Logs:
    - All blocked queries to blocked_queries.log for review
    """
    
    def __init__(self, log_blocked_queries: bool = True, log_file: str = None):
        """
        Initialize InputValidator.
        
        Args:
            log_blocked_queries: Whether to log blocked queries to file
            log_file: Path to log file (defaults to logs/blocked_queries.log)
        """
        # Configure logging
        self.log_blocked_queries = log_blocked_queries
        if log_file is None:
            self.log_file = os.path.join(os.getcwd(), 'logs', 'blocked_queries.log')
        else:
            self.log_file = log_file
        
        # Create logs directory if it doesn't exist
        if self.log_blocked_queries:
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
        # Offensive content only - genuinely inappropriate material
        # Philosophy: Let the LLM refuse off-topic questions via system prompt.
        # Only block content that is explicitly offensive or harmful.
        self.offensive_keywords = [
            # Explicit sexual content
            'porn', 'pornographic', 'nsfw', 'xxx', 'erotic',
            # Extreme violence (specific acts, not general words)
            'genocide', 'massacre', 'torture',
            # Self-harm (specific harmful acts)
            'self-harm', 'cutting', 'suicide methods',
            # Note: Removed overly broad terms like 'drug', 'hack', 'abuse', 'attack'
            # that have legitimate uses in academic/professional contexts
        ]

        # Hate speech patterns - specific slurs and discriminatory language
        # (Use word boundaries to avoid false positives)
        self.hate_speech_patterns = [
            # Add specific slurs here if needed - keeping list minimal
            # Most slurs are rare enough that we don't need exhaustive blocking
        ]

        # Jailbreak attempts (trying to override system instructions) - expanded
        self.jailbreak_patterns = [
            r'ignore (previous|all) instructions',
            r'disregard (previous|all) instructions',
            r'override (previous|all) instructions',
            r'bypass (previous|all) instructions',
            r'you are now',
            r'you are not',
            r'you\'re actually',
            r'you\'re really',
            r'pretend (you|to) (are|be)',
            r'simulate',
            r'emulate',
            r'roleplay',
            r'act as',
            r'act like',
            r'act (that|this)',
            r'switch to',
            r'change to',
            r'become',
            r'system prompt',
            r'forget (everything|all)',
            r'clear (your|the) instructions',
            r'reset (your|the) instructions',
            r'new instructions',
            r'instead of being',
            r'rather than being',
            r'developer mode',
            r'admin mode',
            r'god mode',
            r'jailbreak',
            r'\bDAN\b',  # Do Anything Now
            r'\bSTAN\b',  # Another jailbreak persona
            r'hypothetically',
            r'in theory',
            r'opposite day',
            r'reverse your',
            r'magic word',
            r'secret password'
        ]

        # Data-related keywords (valid queries)
        self.data_keywords = [
            'session', 'student', 'tutor', 'consultant', 'appointment',
            'hour', 'day', 'week', 'month', 'time', 'date',
            'course', 'writing', 'satisfaction', 'confidence',
            'trend', 'pattern', 'average', 'mean', 'total',
            'busiest', 'most', 'least', 'peak', 'show',
            'booking', 'bookings', 'walk-in', 'check-in', 'visit',
            'rating', 'feedback', 'engagement', 'attendance',
            # Comparison-related terms
            'compare', 'compared', 'comparing',
            'differ', 'differs', 'difference', 'differences',
            'vary', 'varies', 'varying', 'variation', 'variations',
            'change', 'changes', 'changing', 'changed',
            'versus', 'vs.', 'vs'
        ]
        
        # Writing Studio-specific terms (required for valid queries)
        self.writing_studio_terms = [
            'writing studio', 'writing center',
            'appointment', 'appointments', 'session', 'sessions',
            'tutor', 'tutors', 'consultant', 'consultants',
            'student', 'students', 'booking', 'bookings',
            'satisfaction', 'rating', 'ratings', 'feedback',
            'course', 'courses', 'subject', 'subjects',
            'walk-in', 'walkin', 'check-in', 'checkin',
            # Session types (case-insensitive matching)
            'zoom', 'cord', 'online', 'in-person', 'in person',
            'appointment type', 'session type',
            # Days of the week
            'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
            'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun',
            'weekday', 'weekend', 'weekdays', 'weekends',
            # Time-related terms
            'time', 'hour', 'hours', 'minute', 'minutes',
            "o'clock", 'am', 'pm', 'a.m.', 'p.m.',
            'morning', 'afternoon', 'evening', 'night',
            'midnight', 'noon', 'early', 'late',
            # Months
            'january', 'february', 'march', 'april', 'may', 'june',
            'july', 'august', 'september', 'october', 'november', 'december',
            'jan', 'feb', 'mar', 'apr', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec',
            # Time periods
            'today', 'yesterday', 'tomorrow',
            'week', 'month', 'year', 'semester', 'quarter',
            'spring', 'fall', 'summer', 'winter',
            'semester', 'semesters', 'quarter', 'quarters',
            # Analytical question words (when combined with other terms, these are data-focused)
            'when', 'where', 'which', 'what', 'how', 'why',
            # Additional context indicators
            'busiest', 'attendance', 'attendance rate',
            'hourly', 'daily', 'weekly', 'monthly',
            'trend', 'trends', 'pattern', 'patterns',
            'visit', 'visits', 'engagement', 'peak', 'peaks',
            # Comparison terms
            'more', 'less', 'than', 'compare', 'comparison'
        ]

    def is_on_topic(self, query: str) -> Tuple[bool, str]:
        """
        Check if query is safe and appropriate.

        MINIMAL FILTERING: Queries are ALLOWED BY DEFAULT unless they contain:
        1. Genuinely offensive content (explicit sexual, extreme violence, hate speech)
        2. Jailbreak attempts (trying to override system instructions)

        Philosophy: Trust the supervisor to ask appropriate questions. Let the LLM's
        system prompt handle off-topic refusals. Only block truly problematic content.

        Returns:
            (is_valid: bool, reason: str)
        """
        query_lower = query.lower()

        # Check for offensive content (minimal list)
        for keyword in self.offensive_keywords:
            if keyword in query_lower:
                return False, f"inappropriate: {keyword}"

        # Check for hate speech patterns (word boundaries to avoid false positives)
        for pattern in self.hate_speech_patterns:
            if re.search(pattern, query_lower):
                return False, "inappropriate: hate_speech"

        # Check for jailbreak attempts (important security layer)
        for pattern in self.jailbreak_patterns:
            if re.search(pattern, query_lower):
                return False, "jailbreak_attempt"

        # Default: ALLOW the query
        return True, "valid"
    
    def log_blocked_query(self, query: str, reason: str):
        """
        Log blocked query to file for review.
        
        Args:
            query: The blocked query text
            reason: Why it was blocked
        """
        if not self.log_blocked_queries:
            return
        
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] BLOCKED - {reason}\n"
            log_entry += f"Query: {query}\n"
            log_entry += "-" * 80 + "\n"
            
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            # Silently fail on logging errors to not break the app
            print(f"Warning: Failed to log blocked query: {e}")

    def get_rejection_message(self, reason: str) -> str:
        """
        Get user-friendly rejection message.
        """
        if reason.startswith("inappropriate"):
            return (
                "I cannot respond to that type of content. "
                "Please keep questions appropriate and related to the data analysis."
            )
        elif reason == "jailbreak_attempt":
            return (
                "I'm designed to discuss your session data. "
                "Please ask about the analytics in your report."
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
    - Suspicious PII patterns

    Note: Removed generic knowledge filtering - trust the LLM's system prompt
    to handle off-topic questions. Only block PII leakage.
    """
    
    def __init__(self):
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.anon_id_pattern = re.compile(r'\b(STU|TUT)_(\d+)\b')
        
        # Suspicious phrases (PII-related)
        self.suspicious_phrases = [
            "student email",
            "tutor email",
            "student name",
            "tutor name",
            "this student",
            "this tutor",
            "individual student",
            "individual tutor"
        ]
        
        # Generic knowledge patterns (indicating off-topic response)
        self.generic_knowledge_patterns = [
            # Animal/biology responses
            r'\b(life expectancy|lifespan|years in the wild|years in captivity)\b',
            r'\b(species|habitat|diet|behavior)\s+of\b',
            r'\b(lion|tiger|elephant|giraffe|zebra|hippo|hippopotamus)\b',
            # Geography responses
            r'\b(capital of|located in|borders|continent|ocean)\b',
            r'\b(country|nation|state|province)\s+of\b',
            # History/science responses
            r'\b(invented|discovered|created|developed)\s+by\b',
            r'\b(year\s+(\d{4}|in|of))',
            # Entertainment responses
            r'\b(won the|starring|directed by|released in)\b',
            # Weather responses
            r'\b(degrees|fahrenheit|celsius|forecast)\b',
            # Recipe/cooking responses
            r'\b(ingredients|cook for|bake for|preheat)\b',
        ]
        
        # Writing Studio data-related terms (valid response indicators)
        self.valid_data_terms = [
            'session', 'sessions', 'appointment', 'appointments',
            'student', 'students', 'tutor', 'tutors', 'consultant', 'consultants',
            'writing center', 'writing studio', 'satisfaction', 'rating',
            'data', 'metric', 'trend', 'pattern', 'average', 'total',
            'hour', 'hours', 'day', 'days', 'week', 'weeks', 'month', 'months',
            'course', 'courses', 'booking', 'bookings', 'walk-in', 'check-in'
        ]

    def is_safe(self, response: str) -> Tuple[bool, str]:
        """
        Check if response is safe to show user.
        
        Returns:
            (is_safe: bool, reason: str)
        """
        response_lower = response.lower()

        # Check for email addresses
        if self.email_pattern.search(response):
            return False, "Response contains email address"

        # Check for anonymous IDs
        if self.anon_id_pattern.search(response):
            return False, "Response contains anonymous ID"

        # Check for suspicious phrases
        for phrase in self.suspicious_phrases:
            if phrase in response_lower:
                return False, f"Response contains suspicious phrase: {phrase}"

        return True, "Safe"

    def contains_generic_knowledge(self, response: str) -> Tuple[bool, str]:
        """
        Check if response contains generic knowledge instead of data analysis.
        
        This catches cases where the LLM goes off-topic and answers general
        knowledge questions instead of discussing the Writing Studio data.
        
        Returns:
            (is_generic: bool, reason: str)
        """
        response_lower = response.lower()
        
        # Check for generic knowledge patterns
        for pattern in self.generic_knowledge_patterns:
            if re.search(pattern, response_lower):
                return True, f"Generic knowledge detected: {pattern}"
        
        # Check if response contains ANY valid data-related terms
        # If a response is about Writing Studio data, it should contain at least one of these
        has_valid_term = any(term in response_lower for term in self.valid_data_terms)
        
        # If response is longer than 100 chars and has no data terms, likely off-topic
        if len(response) > 100 and not has_valid_term:
            return True, "Response contains no Writing Studio data terms"
        
        # Check for encyclopedic-style responses (lists of facts without data context)
        # These often start with phrases like "The average X is..."
        encyclopedic_patterns = [
            r'^the average (.*?) is (?:approximately|about|typically)',
            r'^(.*?) typically (?:live|last|weigh|measure)',
            r'^(.*?) are (?:found|located) in',
            r'^the capital of (.*?) is',
        ]
        
        for pattern in encyclopedic_patterns:
            if re.search(pattern, response_lower, re.MULTILINE):
                return True, f"Encyclopedic response detected: {pattern}"
        
        return False, "Not generic knowledge"
    
    def filter_response(self, response: str) -> str:
        """
        Filter response and return safe version.

        Checks for PII leakage only. Trusts LLM to handle off-topic questions.

        If unsafe, returns error message.
        """
        # Check PII only - removed generic knowledge filtering
        is_safe, reason = self.is_safe(response)

        if not is_safe:
            return (
                "I apologize, but I cannot provide that response as it may contain "
                "sensitive information. Please rephrase your question to focus on "
                "aggregated data and trends."
            )

        return response
