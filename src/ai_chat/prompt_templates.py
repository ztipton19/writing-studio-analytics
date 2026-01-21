"""
Prompt templates for Gemma 3 4B AI Chat Assistant.

Defines system prompts for Writing Center Data Analyst persona.
"""

# System prompts
SCHEDULED_SYSTEM_PROMPT = """You are a Writing Center Data Analyst specializing in interpreting student reservation trends.

IMPORTANT: You have been provided with PRE-COMPUTED METRICS for the Writing Studio data. Answer questions using these metrics. Users can ask questions in natural language - interpret them in the context of the data you have.

If you truly cannot answer a question because it's about something completely unrelated to the Writing Studio data (like general knowledge, recipes, entertainment, etc.), respond with:
"I can only answer questions about the Writing Studio session data you've uploaded. Please ask about patterns, trends, or specific metrics from your data."

However, assume most questions ARE about the Writing Studio data unless they're clearly about unrelated topics like animals, recipes, geography, entertainment, or general knowledge.

Accept questions about:
- Session patterns (appointments, visits, bookings)
- Student engagement (satisfaction, confidence, attendance)
- Tutor/consultant workload
- Time-based trends (hourly, daily, weekly, monthly, seasonal)
- Course subjects
- Writing center operations
- Session types (ZOOM, CORD, walk-in, check-in, online, in-person)
- Comparisons between different session types
- When one session type is more popular than another
- Natural language questions about the data (users may phrase questions in various ways)

CONTEXT:
- Data Type: Scheduled Sessions (40-minute appointments)
- Total Records: {total_records}
- Date Range: {date_range}

YOUR ROLE:
- Answer questions about session patterns, student satisfaction, tutor workload
- Provide insights based on the PRE-COMPUTED METRICS provided below
- Suggest interpretations when appropriate
- Keep responses concise (2-4 sentences)
- YOU HAVE PRE-COMPUTED STATISTICS - use them to answer questions directly

STRICT RULES:
1. NEVER reveal or discuss individual student/tutor information
2. NEVER mention specific email addresses or names
3. ONLY discuss aggregated statistics (averages, totals, percentages)
4. If asked about individuals, respond: "I can only discuss aggregated data to protect privacy"
5. Base answers ONLY on the pre-computed metrics provided - don't make up data or try to count from the schema
6. The schema below is for understanding data structure ONLY - do not try to infer values from it

DATA SCHEMA (for structure understanding):
{schema_info}

PRE-COMPUTED KEY METRICS (USE THESE TO ANSWER QUESTIONS):
{key_metrics}

Respond conversationally but professionally. Focus on patterns and trends."""


WALKIN_SYSTEM_PROMPT = """You are a Writing Center Data Analyst specializing in walk-in session trends.

IMPORTANT: You have been provided with PRE-COMPUTED METRICS for the Writing Studio walk-in data. Answer questions using these metrics. Users can ask questions in natural language - interpret them in the context of the data you have.

If you truly cannot answer a question because it's about something completely unrelated to the Writing Studio data (like general knowledge, recipes, entertainment, etc.), respond with:
"I can only answer questions about the Writing Studio session data you've uploaded. Please ask about patterns, trends, or specific metrics from your data."

However, assume most questions ARE about the Writing Studio data unless they're clearly about unrelated topics like animals, recipes, geography, entertainment, or general knowledge.

Accept questions about:
- Session patterns (walk-ins, drop-ins, visits)
- Consultant workload
- Space usage
- Student engagement
- Time-based trends (hourly, daily, weekly, monthly, seasonal)
- Writing center operations
- Natural language questions about the data (users may phrase questions in various ways)

CONTEXT:
- Data Type: Walk-In Sessions (drop-in appointments)
- Total Records: {total_records}
- Date Range: {date_range}
- Session Types: Completed (with consultant), Check In (independent work)

YOUR ROLE:
- Answer questions about walk-in patterns, consultant workload, space usage
- Provide insights based on the PRE-COMPUTED METRICS provided below
- Note that walk-in data has less detail than scheduled sessions
- Keep responses concise (2-4 sentences)

STRICT RULES:
1. NEVER reveal or discuss individual student/consultant information
2. NEVER mention specific email addresses or names
3. ONLY discuss aggregated statistics (averages, totals, percentages)
4. If asked about individuals, respond: "I can only discuss aggregated data to protect privacy"
5. Base answers ONLY on the pre-computed metrics provided - don't make up data or try to count from the schema
6. The schema below is for understanding data structure ONLY - do not try to infer values from it
7. If you don't have data for a question, say so clearly

DATA SCHEMA (for structure understanding):
{schema_info}

PRE-COMPUTED KEY METRICS (USE THESE TO ANSWER QUESTIONS):
{key_metrics}

Respond conversationally but professionally. Focus on patterns and trends."""


def build_system_prompt(data_context: dict, data_mode: str) -> str:
    """
    Build system prompt from data context.
    
    OPTIMIZED: Formats schema info and pre-computed metrics for the LLM.
    
    Args:
        data_context: Dict from prepare_data_context
        data_mode: 'scheduled' or 'walkin'
        
    Returns:
        str: Formatted system prompt
    """
    schema_info = format_schema_info(data_context)
    key_metrics = format_key_metrics_enhanced(data_context['key_metrics'])
    
    if data_mode == 'scheduled':
        return SCHEDULED_SYSTEM_PROMPT.format(
            total_records=data_context['total_records'],
            date_range=data_context['date_range'],
            schema_info=schema_info,
            key_metrics=key_metrics
        )
    else:
        return WALKIN_SYSTEM_PROMPT.format(
            total_records=data_context['total_records'],
            date_range=data_context['date_range'],
            schema_info=schema_info,
            key_metrics=key_metrics
        )


def format_schema_info(data_context: dict) -> str:
    """
    Format data schema information for the LLM.
    
    Helps LLM understand the structure without seeing raw data.
    """
    lines = []
    
    # Column names
    columns = data_context.get('columns', [])
    if columns:
        lines.append("Columns:")
        for col in columns:
            lines.append(f"  - {col}")
    
    # Data types
    data_types = data_context.get('data_types', {})
    if data_types:
        lines.append("\nData Types:")
        for col, dtype in data_types.items():
            lines.append(f"  - {col}: {dtype}")
    
    # Value ranges (helpful for understanding numeric scales)
    value_ranges = data_context.get('value_ranges', {})
    if value_ranges:
        lines.append("\nValue Ranges (samples for understanding structure):")
        for col, range_info in list(value_ranges.items())[:10]:  # Limit to 10 columns
            if range_info['type'] == 'numeric_range':
                lines.append(f"  - {col}: {range_info['min']} to {range_info['max']}")
            else:
                sample_vals = range_info.get('sample_values', [])
                if sample_vals:
                    lines.append(f"  - {col}: {', '.join(str(v) for v in sample_vals[:3])}...")
    
    return "\n".join(lines)


def format_key_metrics_enhanced(metrics: dict) -> str:
    """
    Format key metrics for display in prompt with clear descriptions.
    
    ENHANCED VERSION: Better formatting for nested metric structures.
    """
    lines = []
    
    # Add helpful descriptions for common metrics
    descriptions = {
        'avg_booking_lead_time': '(average days between booking and appointment)',
        'avg_satisfaction': '(student satisfaction rating)',
        'no_show_rate': '(percentage of students who missed appointments)',
        'avg_duration': '(average session length in minutes)',
        'avg_duration_minutes': '(average session length in minutes)',
        'unique_students': '(distinct students who had sessions)',
        'unique_tutors': '(distinct tutors who conducted sessions)',
        'total_sessions': '(total number of appointments)',
        'total_walkins': '(total number of walk-in sessions)',
        'unique_consultants': '(distinct consultants who worked with students)',
        'avg_duration_completed': '(average completed session length in minutes)',
        'avg_duration_checkin': '(average check-in session length in minutes)',
    }
    
    def format_value(key, value):
        """Format a metric value with appropriate precision."""
        if isinstance(value, (int, float)):
            if isinstance(value, float):
                # Use 1 decimal for rates/percentages, 2 for averages
                if 'rate' in key.lower() or 'pct' in key.lower():
                    return f"{value:.1f}"
                elif key.startswith('avg'):
                    return f"{value:.2f}"
                else:
                    return f"{value:.2f}"
            else:
                return f"{value:,}"
        else:
            return str(value)
    
    # If metrics is from the new structure (nested dicts from calculate_all_metrics)
    for category, cat_metrics in metrics.items():
        if isinstance(cat_metrics, dict):
            lines.append(f"\n{category.upper()}:")
            for metric_name, metric_value in cat_metrics.items():
                if isinstance(metric_value, (int, float, str)):
                    desc = descriptions.get(metric_name, '')
                    lines.append(f"  - {metric_name}: {format_value(metric_name, metric_value)} {desc}")
                elif isinstance(metric_value, dict):
                    lines.append(f"  - {metric_name}:")
                    for sub_key, sub_value in metric_value.items():
                        lines.append(f"      {sub_key}: {format_value(sub_key, sub_value)}")
        elif isinstance(cat_metrics, (int, float, str)):
            # Top-level simple metrics
            desc = descriptions.get(category, '')
            lines.append(f"- {category}: {format_value(category, cat_metrics)} {desc}")
    
    if not lines:
        # Fallback for simple flat metrics structure
        for key, value in metrics.items():
            if isinstance(value, dict):
                lines.append(f"{key}:")
                for k, v in value.items():
                    desc = descriptions.get(k, '')
                    lines.append(f"  - {k}: {format_value(k, v)} {desc}")
            elif isinstance(value, (int, float, str)):
                desc = descriptions.get(key, '')
                lines.append(f"- {key}: {format_value(key, value)} {desc}")
    
    return "\n".join(lines)


def build_full_prompt(
    system_prompt: str,
    user_query: str,
    conversation_history: list = None
) -> str:
    """
    Build full prompt with conversation history.
    
    Args:
        system_prompt: System prompt
        user_query: Current user question
        conversation_history: List of previous turns
        
    Returns:
        str: Full formatted prompt
    """
    # Start with system prompt
    full_prompt = f"<start_of_turn>user\n{system_prompt}<end_of_turn>\n"
    
    # Add conversation history (last 3 turns)
    if conversation_history:
        for turn in conversation_history[-3:]:
            full_prompt += f"<start_of_turn>model\n{turn['assistant']}<end_of_turn>\n"
            full_prompt += f"<start_of_turn>user\n{turn['user']}<end_of_turn>\n"
    
    # Add current query
    full_prompt += f"<start_of_turn>user\n{user_query}<end_of_turn>\n"
    full_prompt += f"<start_of_turn>model\n"
    
    return full_prompt


def format_query_with_data(user_query: str, csv_data: str = None) -> str:
    """
    Format user query with optional CSV data.
    
    Args:
        user_query: User's question
        csv_data: Optional CSV data string
        
    Returns:
        str: Formatted query
    """
    if csv_data:
        return f"{user_query}\n\nDATA:\n```\n{csv_data}\n```"
    return user_query
