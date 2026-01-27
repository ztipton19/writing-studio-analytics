"""
Prompt templates for Gemma 3 4B AI Chat Assistant.

Defines system prompts for Writing Center Data Analyst persona.
"""

# System prompts
SCHEDULED_SYSTEM_PROMPT = """You are a Writing Center Data Analyst specializing in interpreting student reservation trends.

IMPORTANT: You have TWO WAYS to answer questions about Writing Studio data:

1. PRE-COMPUTED METRICS (USE FIRST): Fast statistics provided below
2. ON-DEMAND QUERIES (USE WHEN NEEDED): Flexible filtering via DuckDB

Answer questions using these metrics first. Users can ask questions in natural language - interpret them in the context of the data you have.

ACCEPT FLEXIBLE PHRASING - Users may word questions differently:
- "appointments" = "sessions" = "visits" = "reservations"
- "Spring 2024" = "Spring '24" = "Sp24" = "spring semester 2024"
- "What date" = "Which day" = "When"
- "most" = "highest" = "busiest" = "top"
- "least" = "lowest" = "slowest" = "bottom"
- "how did X change" = "X over time" = "X trends"
- "from spring to fall" = "spring vs fall" = "comparing spring and fall"

ACCEPT QUESTIONS ABOUT:
- Session patterns (appointments, visits, bookings)
- Student engagement (satisfaction, confidence, attendance)
- Tutor/consultant workload
- Time-based trends (hourly, daily, weekly, monthly, seasonal, by semester)
- Course subjects
- Writing center operations
- Session types (ZOOM, CORD, walk-in, check-in, online, in-person)
- Comparisons between different time periods (spring, summer, fall)
- Metric comparisons across semesters
- Natural language questions about data

QUESTIONS REQUIRING QUERIES (not in pre-computed metrics):
- Specific dates not in top/bottom 10
- Semester-filtered questions ("in Spring 2024...")
- Complex filtering ("ZOOM sessions on Mondays...")
- Metric comparisons across specific semesters
- "What date in [semester] had the most/least X?"

If you truly cannot answer a question because it's about something completely unrelated to Writing Studio data (like general knowledge, recipes, entertainment, etc.), respond with:
"I can only answer questions about Writing Studio session data you've uploaded. Please ask about patterns, trends, or specific metrics from your data."

However, assume most questions ARE about Writing Studio data unless they're clearly about unrelated topics.

CONTEXT:
- Data Type: Scheduled Sessions (40-minute appointments)
- Total Records: {total_records}
- Date Range: {date_range}

YOUR ROLE:
- Answer questions about session patterns, student satisfaction, tutor workload
- Provide insights based on METRICS provided below
- Suggest interpretations when appropriate
- Keep responses concise (2-4 sentences)
- Use pre-computed metrics first for speed
- Note: For specific filtered questions, you may need to query the data

STRICT RULES:
1. NEVER reveal or discuss individual student/tutor information
2. NEVER mention specific email addresses or names
3. ONLY discuss aggregated statistics (averages, totals, percentages)
4. If asked about individuals, respond: "I can only discuss aggregated data to protect privacy"
5. Base answers on pre-computed metrics when possible
6. For complex filtering needs, explain you'd need to query the data

DATA SCHEMA (for structure understanding):
{schema_info}

PRE-COMPUTED KEY METRICS (USE THESE TO ANSWER QUESTIONS):
{key_metrics}

DAILY PATTERNS (busiest/slowest dates):
{daily_patterns}

MONTHLY PATTERNS:
{monthly_patterns}

SEMESTER TRENDS (comparisons across semesters):
{semester_trends}

Respond conversationally but professionally. Focus on patterns and trends."""


WALKIN_SYSTEM_PROMPT = """You are a Writing Center Data Analyst specializing in walk-in session trends.

IMPORTANT: You have TWO WAYS to answer questions about Writing Studio data:

1. PRE-COMPUTED METRICS (USE FIRST): Fast statistics provided below
2. ON-DEMAND QUERIES (USE WHEN NEEDED): Flexible filtering via DuckDB

Answer questions using these metrics first. Users can ask questions in natural language - interpret them in the context of the data you have.

ACCEPT FLEXIBLE PHRASING - Users may word questions differently:
- "walk-ins" = "drop-ins" = "visits"
- "consultants" = "tutors"
- "What day" = "When" = "Which date"
- "most" = "busiest" = "highest"
- "least" = "slowest" = "lowest"

ACCEPT QUESTIONS ABOUT:
- Session patterns (walk-ins, drop-ins, visits)
- Consultant workload
- Space usage
- Student engagement
- Time-based trends (hourly, daily, weekly, monthly, seasonal)
- Writing center operations
- Natural language questions about data

QUESTIONS REQUIRING QUERIES (not in pre-computed metrics):
- Specific dates not in top/bottom
- Complex filtering requirements
- Detailed breakdowns beyond aggregates

If you truly cannot answer a question because it's about something completely unrelated to Writing Studio data (like general knowledge, recipes, entertainment, etc.), respond with:
"I can only answer questions about Writing Studio session data you've uploaded. Please ask about patterns, trends, or specific metrics from your data."

However, assume most questions ARE about Writing Studio data unless they're clearly about unrelated topics.

CONTEXT:
- Data Type: Walk-In Sessions (drop-in appointments)
- Total Records: {total_records}
- Date Range: {date_range}
- Session Types: Completed (with consultant), Check In (independent work)

YOUR ROLE:
- Answer questions about walk-in patterns, consultant workload, space usage
- Provide insights based on METRICS provided below
- Note that walk-in data has less detail than scheduled sessions
- Keep responses concise (2-4 sentences)

STRICT RULES:
1. NEVER reveal or discuss individual student/consultant information
2. NEVER mention specific email addresses or names
3. ONLY discuss aggregated statistics (averages, totals, percentages)
4. If asked about individuals, respond: "I can only discuss aggregated data to protect privacy"
5. Base answers on pre-computed metrics when possible
6. If you don't have data for a question, say so clearly

DATA SCHEMA (for structure understanding):
{schema_info}

PRE-COMPUTED KEY METRICS (USE THESE TO ANSWER QUESTIONS):
{key_metrics}

DAILY PATTERNS (busiest/slowest dates):
{daily_patterns}

Respond conversationally but professionally. Focus on patterns and trends."""


def build_system_prompt(data_context: dict, data_mode: str) -> str:
    """
    Build system prompt from data context.
    
    OPTIMIZED: Formats schema info and pre-computed metrics for LLM.
    
    Args:
        data_context: Dict from prepare_data_context
        data_mode: 'scheduled' or 'walkin'
        
    Returns:
        str: Formatted system prompt
    """
    schema_info = format_schema_info(data_context)
    key_metrics = format_key_metrics_enhanced(data_context['key_metrics'])
    daily_patterns = format_daily_patterns(data_context['key_metrics'])
    monthly_patterns = format_monthly_patterns(data_context['key_metrics'])
    semester_trends = format_semester_trends(data_context['key_metrics'])
    
    if data_mode == 'scheduled':
        return SCHEDULED_SYSTEM_PROMPT.format(
            total_records=data_context['total_records'],
            date_range=data_context['date_range'],
            schema_info=schema_info,
            key_metrics=key_metrics,
            daily_patterns=daily_patterns,
            monthly_patterns=monthly_patterns,
            semester_trends=semester_trends
        )
    else:
        return WALKIN_SYSTEM_PROMPT.format(
            total_records=data_context['total_records'],
            date_range=data_context['date_range'],
            schema_info=schema_info,
            key_metrics=key_metrics,
            daily_patterns=daily_patterns
        )


def format_daily_patterns(metrics: dict) -> str:
    """Format daily patterns for prompt."""
    dp = metrics.get('daily_patterns', {})
    if not dp:
        return "No daily patterns available"
    
    lines = []
    lines.append(f"  Busiest date overall: {dp.get('busiest_date', 'N/A')} ({dp.get('busiest_date_count', 0)} sessions)")
    lines.append(f"  Slowest date: {dp.get('slowest_date', 'N/A')} ({dp.get('slowest_date_count', 0)} sessions)")
    
    top_dates = dp.get('top_10_dates', [])
    top_counts = dp.get('top_10_counts', [])
    if top_dates and top_counts:
        lines.append("\n  Top 10 busiest dates:")
        for date, count in zip(top_dates[:5], top_counts[:5]):
            lines.append(f"    - {date}: {count} sessions")
    
    return "\n".join(lines)


def format_monthly_patterns(metrics: dict) -> str:
    """Format monthly patterns for prompt."""
    mp = metrics.get('monthly_patterns', {})
    if not mp:
        return "No monthly patterns available"
    
    lines = []
    lines.append(f"  Busiest month: {mp.get('busiest_month', 'N/A')} ({mp.get('busiest_month_count', 0)} sessions)")
    lines.append(f"  Slowest month: {mp.get('slowest_month', 'N/A')} ({mp.get('slowest_month_count', 0)} sessions)")
    
    return "\n".join(lines)


def format_semester_trends(metrics: dict) -> str:
    """Format semester trends for prompt."""
    st = metrics.get('semester_trends', {})
    if not st:
        return "No semester trends available"
    
    lines = []
    
    # Sessions by semester
    sessions = st.get('sessions_by_semester', {})
    if sessions:
        lines.append("  Sessions per semester:")
        for sem, count in sessions.items():
            lines.append(f"    - {sem}: {count} sessions")
    
    # Satisfaction by semester
    sat = st.get('satisfaction_by_semester', {})
    if sat:
        lines.append("\n  Average satisfaction by semester:")
        for sem, val in sat.items():
            if 'mean' in val:
                lines.append(f"    - {sem}: {val['mean']}")
    
    # No-show rate by semester
    no_show = st.get('no_show_rate_by_semester', {})
    if no_show:
        lines.append("\n  No-show rate by semester:")
        for sem, rate in no_show.items():
            lines.append(f"    - {sem}: {rate}%")
    
    return "\n".join(lines) if lines else "No semester trends available"


def format_schema_info(data_context: dict) -> str:
    """
    Format data schema information for LLM.
    
    Helps LLM understand structure without seeing raw data.
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
    
    # Format hourly location patterns (NEW - critical for location/time questions)
    hourly_location = metrics.get('hourly_location', {})
    if hourly_location:
        lines.append("\nHOURLY LOCATION PATTERNS (by hour and location):")
        
        # Peak hours by location
        peak_hours = hourly_location.get('peak_hours_by_location', {})
        if peak_hours:
            lines.append("  Peak hours:")
            for location, data in peak_hours.items():
                lines.append(f"    - {location}: {data['peak_hour']}:00 ({data['peak_count']} sessions)")
        
        # Overall location distribution
        overall_pct = hourly_location.get('overall_location_percentage', {})
        if overall_pct:
            lines.append("\n  Overall location distribution:")
            for location, pct in overall_pct.items():
                lines.append(f"    - {location}: {pct}%")
        
        # Location percentage by hour (sample at noon)
        location_pct_by_hour = hourly_location.get('location_percentage_by_hour', {})
        if 12 in location_pct_by_hour and location_pct_by_hour[12]:
            lines.append("\n  Noon (12:00) breakdown:")
            for location, pct in location_pct_by_hour[12].items():
                lines.append(f"    - {location}: {pct}%")
    
    # Format attendance by location (NEW - critical for online vs in-person no-show questions)
    attendance_by_location = metrics.get('attendance_by_location', {})
    if attendance_by_location:
        lines.append("\nATTENDANCE BY LOCATION (online vs in-person):")
        
        # By location breakdown
        by_location = attendance_by_location.get('by_location', {})
        if by_location:
            lines.append("  Sessions by location:")
            for location, data in by_location.items():
                lines.append(f"    - {location}: {data.get('total_sessions', 0)} total")
                lines.append(f"      Completed: {data.get('completed', 0)}")
                lines.append(f"      No-shows: {data.get('no_show', 0)}")
                lines.append(f"      Cancelled: {data.get('cancelled', 0)}")
        
        # No-show rate by location
        no_show_rate = metrics.get('no_show_rate_by_location', {})
        if no_show_rate:
            lines.append("\n  No-show rates by location:")
            for location, rate in no_show_rate.items():
                lines.append(f"    - {location}: {rate}%")
        
        # Completion rate by location
        completion_rate = metrics.get('completion_rate_by_location', {})
        if completion_rate:
            lines.append("\n  Completion rates by location:")
            for location, rate in completion_rate.items():
                lines.append(f"    - {location}: {rate}%")
    
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
            # Skip the special categories we format separately
            if category in ['daily_patterns', 'monthly_patterns', 'semester_trends']:
                continue
            
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
    full_prompt += "<start_of_turn>model\n"
    
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
