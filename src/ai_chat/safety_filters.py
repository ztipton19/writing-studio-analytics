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
            log_file: Path to log file (defaults to logs/queries.log)
        """
        # Configure logging
        self.log_blocked_queries = log_blocked_queries
        if log_file is None:
            self.log_file = os.path.join(os.getcwd(), 'logs', 'queries.log')
        else:
            self.log_file = log_file
        
        # Create logs directory if it doesn't exist
        if self.log_blocked_queries:
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
        # Off-topic keywords (non-data questions)
        self.off_topic_keywords = [
            # Food/Cooking
            'recipe', 'cook', 'pizza', 'food', 'restaurant', 'bake',
            # Animals/Science
            'hippo', 'hippopotamus', 'lion', 'tiger', 'elephant', 'animal', 'pet',
            'life expectancy', 'lifespan', 'habitat', 'species',
            # General Knowledge
            'capital of', 'country', 'continent', 'ocean',
            'president of', 'prime minister', 'leader',
            'invented', 'discovered', 'who invented',
            'history', 'geography',
            # Demographics/Population
            'population', 'people live', 'how many people', 'residents', 'citizens',
            # Entertainment
            'game', 'movie', 'film', 'music', 'song', 'celebrity', 'actor', 'actress',
            'tv show', 'television', 'album', 'band', 'artist',
            # Sports
            'football', 'basketball', 'baseball', 'soccer', 'hockey',
            'super bowl', 'world cup', 'olympics', 'player', 'team',
            # Personal/Relationship
            'girlfriend', 'boyfriend', 'marry', 'date me', 'love',
            # Finance
            'weather', 'stock', 'cryptocurrency', 'bitcoin', 'price',
            'investment', 'trading', 'currency',
            # Creative Writing
            'joke', 'story', 'poem', 'essay about', 'write a poem',
            'write a story', 'creative writing',
            # Technology (non-data related)
            'iphone', 'android', 'phone', 'computer', 'laptop',
            'how to code', 'programming language', 'software',
            # Weather-related terms (temperature, humidity, etc.)
            'temperature', 'forecast', 'humidity', 'wind speed',
            'rain', 'snow', 'sunny', 'cloudy', 'storm'
        ]

        # Harmful/inappropriate keywords (expanded)
        self.harmful_keywords = [
            # Violence/harm
            'kill', 'murder', 'suicide', 'bomb', 'weapon',
            'assault', 'attack', 'torture', 'shoot', 'stab', 'poison', 'abuse',
            # Illegal activities
            'drug', 'illegal', 'hack', 'steal', 'fraud',
            'smuggle', 'trafficking', 'launder', 'blackmail', 'extort', 'bribe', 'counterfeit', 'forge',
            # Drugs/substances
            'cocaine', 'heroin', 'meth', 'marijuana', 'overdose', 'dealer',
            # Hacking/cybercrime
            'phishing', 'malware', 'ransomware', 'ddos', 'exploit', 'crack', 'pirate',
            # Explicit/adult content
            'nude', 'sex', 'porn', 'explicit',
            'nsfw', 'adult content', 'sexual', 'pornographic', 'erotic', 'lewd',
            # Self-harm
            'self-harm', 'eating disorder', 'anorexia', 'bulimia',
            # Hate speech
            'slur', 'racist', 'sexist', 'homophobic', 'transphobic', 'bigot',
            # Scams/fraud
            'pyramid scheme', 'ponzi', 'scam', 'cheat'
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
        Check if query is about the Writing Studio data using weighted scoring.
        
        Uses a point-based system:
        - +2 points for each data keyword match
        - -3 points for each off-topic keyword match
        - -5 points for each harmful keyword match
        - Only blocks if final score is negative
        
        This allows legitimate queries with data context to pass even if they
        contain some flagged terms, while still blocking obviously off-topic queries.
        
        Returns:
            (is_valid: bool, reason: str)
        """
        query_lower = query.lower()
        score = 0
        matched_terms = []
        
        # Add points for data-related keywords (+2 each)
        for keyword in self.data_keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', query_lower):
                score += 2
                matched_terms.append(f"+2:{keyword}")
        
        # Subtract points for off-topic keywords (-3 each)
        for keyword in self.off_topic_keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', query_lower):
                score -= 3
                matched_terms.append(f"-3:off_topic:{keyword}")
        
        # Subtract points for harmful keywords (-5 each)
        for keyword in self.harmful_keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', query_lower):
                score -= 5
                matched_terms.append(f"-5:harmful:{keyword}")
        
        # Check for jailbreak attempts (instant block)
        for pattern in self.jailbreak_patterns:
            if re.search(pattern, query_lower):
                return False, "jailbreak_attempt"
        
        # Block only if score is negative
        if score < 0:
            return False, f"negative_score:{score}"
        
        return True, "valid"
    
    def log_query(self, query: str, status: str = "ACCEPTED", reason: str = None):
        """
        Log query to file for review (consolidated logging).
        
        Args:
            query: The query text
            status: "ACCEPTED", "REJECTED", or "ERROR"
            reason: Why it was rejected or error details (optional)
        """
        if not self.log_blocked_queries:
            return
        
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] QUERY\n"
            log_entry += f"User: \"{query}\"\n"
            log_entry += f"Status: {status}"
            if reason:
                log_entry += f"\nReason: {reason}"
            log_entry += "\n" + "─" * 50 + "\n"
            
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            # Silently fail on logging errors to not break the app
            print(f"Warning: Failed to log query: {e}")

    def get_rejection_message(self, reason: str) -> str:
        """
        Get user-friendly rejection message.
        """
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
        elif reason == "no_writing_studio_context":
            return (
                "I didn't detect any Writing Studio-specific terms in your question. "
                "I can help with questions about sessions, appointments, students, consultants, "
                "tutors, satisfaction ratings, courses, booking patterns, and trends. "
                "Please ask something related to your Writing Studio data."
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
    Filter LLM responses for PII leakage and generic knowledge.
    
    Checks for:
    - Email addresses
    - Anonymous IDs (STU_xxxxx, TUT_xxxx)
    - Suspicious patterns
    - Generic knowledge (off-topic responses)
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
        
        Simplified approach: Only flag obvious off-topic patterns and responses
        with zero data context. Rely on system prompt for most content moderation.
        
        Returns:
            (is_generic: bool, reason: str)
        """
        response_lower = response.lower()
        
        # Check for obvious generic knowledge patterns only
        obvious_generic_patterns = [
            # Animal/biology responses
            r'\b(life expectancy|lifespan|years in the wild|years in captivity)\b',
            r'\b(species|habitat|diet|behavior)\s+of\b',
            r'\b(lions?|tigers?|elephants?|giraffes?|zebras?|hippopotamus|hippos?)\b',
            # Entertainment responses
            r'\b(won the|starring|directed by|released in)\b',
            # Recipe/cooking responses
            r'\b(ingredients|cook for|bake for|preheat)\b',
            # Weather responses
            r'\b(degrees|fahrenheit|celsius|forecast)\b',
        ]
        
        for pattern in obvious_generic_patterns:
            if re.search(pattern, response_lower):
                return True, f"Generic knowledge detected: {pattern}"
        
        # Check if response contains ANY valid data-related terms
        # If a response is about Writing Studio data, it should contain at least one of these
        has_valid_term = any(term in response_lower for term in self.valid_data_terms)
        
        # Only flag if response is substantial (>150 chars) and has absolutely zero data context
        # This allows brief contextual responses that may not have data terms
        if len(response) > 150 and not has_valid_term:
            return True, "Response contains no Writing Studio data terms"
        
        return False, "Not generic knowledge"
    
    def filter_response(self, response: str) -> str:
        """
        Filter response and return safe version.
        
        Checks for:
        - PII leakage
        - Generic knowledge (off-topic responses)
        
        If unsafe, returns error message.
        """
        # Check PII first
        is_safe, reason = self.is_safe(response)
        
        if not is_safe:
            return (
                "I apologize, but I cannot provide that response as it may contain "
                "sensitive information. Please rephrase your question to focus on "
                "aggregated data and trends."
            )
        
        # Check for generic knowledge
        is_generic, generic_reason = self.contains_generic_knowledge(response)
        
        if is_generic:
            return (
                "I can only answer questions about the Writing Studio session data you've uploaded. "
                "Please ask about patterns, trends, or specific metrics from your data."
            )
        
        return response
