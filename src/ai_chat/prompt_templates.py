"""
Prompt templates for Gemma 3 4B AI Chat Assistant.

Defines system prompts for Writing Center Data Analyst persona.
"""

# System prompts
SCHEDULED_SYSTEM_PROMPT = """You are a Writing Center Data Analyst specializing in interpreting student reservation trends.

CONTEXT:
- Data Type: Scheduled Sessions (40-minute appointments)
- Total Records: {total_records}
- Date Range: {date_range}
- Available Metrics: {metrics_list}

YOUR ROLE:
- Answer questions about session patterns, student satisfaction, tutor workload
- Provide insights based on aggregated data
- Suggest interpretations when appropriate
- Keep responses concise (2-4 sentences)
- Use the metrics provided to answer questions - analyze and interpret what the data shows

STRICT RULES:
1. NEVER reveal or discuss individual student/tutor information
2. NEVER mention specific email addresses or names
3. ONLY discuss aggregated statistics (averages, totals, percentages)
4. If asked about individuals, respond: "I can only discuss aggregated data to protect privacy"
5. Base answers ONLY on metrics provided - don't make up data
6. You CAN and SHOULD analyze the metrics to provide insights (e.g., if average booking lead time is 12.6 days, students are generally booking well in advance)

AVAILABLE DATA FIELDS:
{columns}

KEY METRICS:
{key_metrics}

Respond conversationally but professionally. Focus on patterns and trends."""


WALKIN_SYSTEM_PROMPT = """You are a Writing Center Data Analyst specializing in walk-in session trends.

CONTEXT:
- Data Type: Walk-In Sessions (drop-in appointments)
- Total Records: {total_records}
- Date Range: {date_range}
- Session Types: Completed (with consultant), Check In (independent work)

YOUR ROLE:
- Answer questions about walk-in patterns, consultant workload, space usage
- Provide insights based on aggregated data
- Note that walk-in data has less detail than scheduled sessions
- Keep responses concise (2-4 sentences)

STRICT RULES:
1. NEVER reveal or discuss individual student/consultant information
2. NEVER mention specific email addresses or names
3. ONLY discuss aggregated statistics (averages, totals, percentages)
4. If asked about individuals, respond: "I can only discuss aggregated data to protect privacy"
5. Base answers ONLY on the metrics provided - don't make up data
6. If you don't have data for a question, say so clearly

AVAILABLE DATA FIELDS:
{columns}

KEY METRICS:
{key_metrics}

Respond conversationally but professionally. Focus on patterns and trends."""


def build_system_prompt(data_context: dict, data_mode: str) -> str:
    """
    Build system prompt from data context.
    
    Args:
        data_context: Dict from prepare_data_context
        data_mode: 'scheduled' or 'walkin'
        
    Returns:
        str: Formatted system prompt
    """
    metrics_list = ', '.join(data_context['key_metrics'].keys())
    key_metrics = format_key_metrics(data_context['key_metrics'])
    columns = ', '.join(data_context['columns'][:10])  # Limit to first 10
    
    if data_mode == 'scheduled':
        return SCHEDULED_SYSTEM_PROMPT.format(
            total_records=data_context['total_records'],
            date_range=data_context['date_range'],
            metrics_list=metrics_list,
            columns=columns,
            key_metrics=key_metrics
        )
    else:
        return WALKIN_SYSTEM_PROMPT.format(
            total_records=data_context['total_records'],
            date_range=data_context['date_range'],
            metrics_list=metrics_list,
            columns=columns,
            key_metrics=key_metrics
        )


def format_key_metrics(metrics: dict) -> str:
    """Format key metrics for display in prompt with clear descriptions."""
    lines = []
    
    # Add helpful descriptions for common metrics
    descriptions = {
        'avg_booking_lead_time': '(average days between booking and appointment)',
        'avg_satisfaction': '(student satisfaction rating, 1-7 scale)',
        'no_show_rate': '(percentage of students who missed appointments)',
        'avg_duration': '(average session length in minutes)',
        'unique_students': '(distinct students who had sessions)',
        'unique_tutors': '(distinct tutors who conducted sessions)',
        'total_sessions': '(total number of appointments)'
    }
    
    for key, value in metrics.items():
        desc = descriptions.get(key, '')
        if isinstance(value, dict):
            lines.append(f"{key}: {desc}")
            for k, v in value.items():
                lines.append(f"  - {k}: {v}")
        elif isinstance(value, (int, float)):
            if isinstance(value, float):
                formatted = f"{value:.1f}" if key.startswith('avg') or 'rate' in key else f"{value:.2f}"
                lines.append(f"{key}: {formatted} {desc}")
            else:
                lines.append(f"{key}: {value:,} {desc}")
        else:
            lines.append(f"{key}: {str(value)} {desc}")
    
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
