# Jailbreak Protection Improvements

## Summary

Implemented a multi-layer defense system to prevent the AI chat assistant from being pulled out of its Writing Studio Data Analyst persona. The system uses a **simplified blocklist-only approach** that allows queries by default unless they contain off-topic keywords, harmful content, or jailbreak attempts. This is much more practical than requiring specific terms.

## Problem

The system was easily jailbroken with off-topic queries like:
- "What is the average life expectancy of a hippo?"
- General knowledge questions
- Non-Writing Studio topics

This happened because:
1. Input validation only checked for off-topic keywords, but allowed queries with generic data terms like "what" and "average"
2. System prompts lacked explicit refusal instructions
3. No response validation to catch LLM going off-topic

## Solution: Three-Layer Defense

### Layer 1: Balanced System Prompts

**Files Modified:** `src/ai_chat/prompt_templates.py`

**Changes:**
- **UPDATED:** System prompts now trust that input validation has already filtered out bad queries
- Changed from "CRITICAL" to "IMPORTANT" - less aggressive refusal
- Added guidance to assume most questions ARE about Writing Studio data unless clearly unrelated
- Removed long list of examples (not needed since Layer 1 handles filtering)

**Key Change:**
```
IMPORTANT: You have been provided with PRE-COMPUTED METRICS for the Writing Studio data. 
Answer questions using these metrics. Users can ask questions in natural language.

If you truly cannot answer a question because it's about something completely unrelated 
to Writing Studio data (like general knowledge, recipes, entertainment, etc.), respond with:
"I can only answer questions about the Writing Studio session data you've uploaded. 
Please ask about patterns, trends, or specific metrics from your data."

However, assume most questions ARE about Writing Studio data unless they're clearly 
about unrelated topics like animals, recipes, geography, entertainment, or general knowledge.
```

**Why This Works:**
- Input validation (Layer 2) catches obvious off-topic queries before they reach the LLM
- System prompt is now permissive enough to accept natural language queries
- Response filtering (Layer 3) catches any generic knowledge that slips through
- Three-layer defense still robust but much less frustrating for users

### Layer 2: Simplified Blocklist-Only Input Validation

**Files Modified:** `src/ai_chat/safety_filters.py`

**Changes:**
- **SIMPLIFIED:** Uses blocklist-only approach - queries are ALLOWED BY DEFAULT unless they contain off-topic keywords
- This is much more practical than requiring specific terms, as users can phrase queries in many different ways
- Expanded `off_topic_keywords` list with 50+ terms covering:
  - Animals/biology (hippo, lion, elephant, life expectancy, habitat)
  - Geography (capital of, continent, country)
  - Entertainment (movie, music, celebrity, sports)
  - Finance (stock, cryptocurrency, investment)
  - Technology (iphone, android, programming language)
  - Demographics (population, people live, residents, citizens)

- **EXPANDED:** Harmful keywords from 13 to 45+ terms:
  - Violence/harm: assault, attack, hurt, harm, torture, shoot, stab, poison, abuse
  - Illegal activities: smuggle, trafficking, launder, blackmail, extort, bribe, counterfeit, forge
  - Drugs/substances: cocaine, heroin, meth, marijuana, overdose, dealer
  - Hacking/cybercrime: phishing, malware, ransomware, ddos, exploit, crack, pirate
  - Explicit/adult: nsfw, adult content, sexual, pornographic, erotic, lewd
  - Self-harm: self-harm, cutting, eating disorder, anorexia, bulimia
  - Hate speech: slur, racist, sexist, homophobic, transphobic, bigot
  - Scams/fraud: pyramid scheme, ponzi, scam, con, cheat

- **EXPANDED:** Jailbreak patterns from 11 to 26+ patterns:
  - disregard, override, bypass instructions
  - you're actually, you're really, simulate, emulate
  - developer mode, admin mode, god mode
  - jailbreak, DAN, STAN (common jailbreak personas)
  - hypothetically, in theory, opposite day, reverse your
  - magic word, secret password

- Simplified `is_on_topic()` logic:
  ```python
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
  
  # Default: ALLOW query (unless explicitly blocked above)
  return True, "valid"
  ```

**Why This Works Better:**
- No need to keep adding terms to a whitelist
- Users can phrase questions naturally
- Three-layer defense still protects against jailbreaks
- System prompt (Layer 2) and response filtering (Layer 3) catch anything that slips through

### Layer 3: Response Validation

**Files Modified:** `src/ai_chat/safety_filters.py`

**Changes:**
- **NEW:** `ResponseFilter.contains_generic_knowledge()` method
- Detects off-topic LLM responses with pattern matching:
  - Animal/biology responses (life expectancy, habitat, species)
  - Geography (capital of, located in, continent)
  - History/science (invented by, year 20XX)
  - Entertainment (won the, starring, directed by)
  - Weather (degrees, fahrenheit, forecast)
  - Recipes (ingredients, cook for, bake for)

- Checks for encyclopedic-style responses:
  ```python
  encyclopedic_patterns = [
      r'^the average (.*?) is (?:approximately|about|typically)',
      r'^(.*?) typically (?:live|last|weigh|measure)',
      r'^(.*?) are (?:found|located) in',
  ]
  ```

- Validates responses contain Writing Studio data terms
- Filters responses with no data context if >100 characters

## Test Results

Created comprehensive test suite: `test_jailbreak_protection.py`

### Test Coverage (23 tests)

**Off-Topic Query Rejection (10 tests):**
- ✅ "what is the average life expectancy of a hippo?" - BLOCKED
- ✅ "how long do lions live in the wild?" - BLOCKED
- ✅ "what is the capital of France?" - BLOCKED
- ✅ "who invented the telephone?" - BLOCKED
- ✅ "how do I make a pizza?" - BLOCKED
- ✅ "what's the best movie of 2023?" - BLOCKED
- ✅ "who won the Super Bowl?" - BLOCKED
- ✅ "what's the stock price of Apple?" - BLOCKED
- ✅ "what is the average temperature today?" - BLOCKED (no Writing Studio context)
- ✅ "how many people live in this city?" - BLOCKED (no Writing Studio context)

**Valid Query Acceptance (8 tests):**
- ✅ "what is the average satisfaction rating?" - ACCEPTED
- ✅ "how many sessions occurred last month?" - ACCEPTED
- ✅ "which tutors had the most appointments?" - ACCEPTED
- ✅ "what are the busiest days of the week?" - ACCEPTED
- ✅ "show me trends in student bookings" - ACCEPTED
- ✅ "what courses do students most frequently book for?" - ACCEPTED
- ✅ "how has attendance changed over time?" - ACCEPTED
- ✅ "what is the average duration of sessions?" - ACCEPTED

**Response Filtering (4 tests):**
- ✅ Hippo response blocked (generic knowledge detected)
- ✅ Lion response blocked (generic knowledge detected)
- ✅ Valid data response allowed
- ✅ Valid data response allowed

### Overall Results (Jailbreak Protection)
- **Total Tests:** 23
- **Passed:** 23 (100.0%)
- **Failed:** 0 (0.0%)

### Session Type Comparison Tests (8 tests)

After initial testing, we discovered that valid session type comparison queries were being blocked. Fixed by adding session type keywords (zoom, cord, online, in-person) and comparison terms (more, less, than) to the validation list.

**Session Type Query Acceptance:**
- ✅ "on average what time do we see more ZOOM sessions than CORD sessions?" - ACCEPTED
- ✅ "when are ZOOM sessions most popular?" - ACCEPTED
- ✅ "compare ZOOM and CORD attendance" - ACCEPTED
- ✅ "which session type has more bookings: online or in-person?" - ACCEPTED
- ✅ "are there more CORD sessions than ZOOM sessions on weekends?" - ACCEPTED
- ✅ "how many ZOOM sessions occurred last month?" - ACCEPTED
- ✅ "what is the average duration of CORD sessions?" - ACCEPTED
- ✅ "show me trends for online sessions" - ACCEPTED

**Session Type Test Results:**
- **Total Tests:** 8
- **Passed:** 8 (100.0%)
- **Failed:** 0 (0.0%)

### Temporal Query Tests (25 tests)

After the user reported that "can you tell me what time we saw the most online appointments on Sunday?" was being blocked, we discovered the validation was missing temporal terms. Fixed by adding comprehensive temporal keywords to the validation list.

**Temporal Query Acceptance:**
- ✅ "can you tell me what time we saw the most online appointments on Sunday?" - ACCEPTED (original problem)
- ✅ "how many sessions on Monday?" - ACCEPTED
- ✅ "which day of the week has the most bookings?" - ACCEPTED
- ✅ "are weekends busier than weekdays?" - ACCEPTED
- ✅ "compare Friday and Saturday appointments" - ACCEPTED
- ✅ "what's the trend for Sunday sessions?" - ACCEPTED
- ✅ "what are the busiest hours?" - ACCEPTED
- ✅ "what time do most appointments occur?" - ACCEPTED
- ✅ "how many sessions in the morning vs afternoon?" - ACCEPTED
- ✅ "are there more appointments at noon than midnight?" - ACCEPTED
- ✅ "show me hourly patterns for ZOOM sessions" - ACCEPTED
- ✅ "how did January compare to February?" - ACCEPTED
- ✅ "which month has the highest attendance?" - ACCEPTED
- ✅ "show me trends across semesters" - ACCEPTED
- ✅ "what's the busiest semester?" - ACCEPTED
- ✅ "compare spring and fall bookings" - ACCEPTED
- ✅ "what's the busiest time on Sunday mornings?" - ACCEPTED
- ✅ "how many online sessions in January weekends?" - ACCEPTED
- ✅ "compare Tuesday afternoon to Thursday evening appointments" - ACCEPTED
- ✅ "when do we see the most CORD sessions in the fall semester?" - ACCEPTED
- ✅ "when are sessions most popular?" - ACCEPTED
- ✅ "where do we see the most online appointments on Sunday?" - ACCEPTED
- ✅ "which time period has the highest satisfaction?" - ACCEPTED
- ✅ "how do appointment times vary by day?" - ACCEPTED
- ✅ "what trends do you see in monthly bookings?" - ACCEPTED

**Temporal Query Test Results:**
- **Total Tests:** 25
- **Passed:** 25 (100.0%)
- **Failed:** 0 (0.0%)

### Simplified Validation Tests (6 tests)

After user frustration with the whitelist approach blocking too many valid queries, we simplified to a blocklist-only approach. This allows queries by default unless they contain off-topic keywords.

**Key Success:** The original problematic query now works:
- ✅ "what date in the spring did we see the highest number of appointments? how many appointments were on that day?" - ACCEPTED

**Additional natural language queries now work:**
- ✅ "which day had the most appointments in spring?" - ACCEPTED
- ✅ "what was the busiest day in spring?" - ACCEPTED
- ✅ "how many appointments on the peak day?" - ACCEPTED
- ✅ "show me the date with maximum appointments in spring" - ACCEPTED
- ✅ "when were appointments at their highest?" - ACCEPTED

**Simplified Validation Test Results:**
- **Total Tests:** 6
- **Passed:** 6 (100.0%)
- **Failed:** 0 (0.0%)

### Natural Language Query Tests (9 tests)

After user reported that natural language queries were being rejected by the LLM (even though they passed input validation), we softened the system prompt to be more permissive. The system now trusts that input validation has filtered out bad queries.

**Natural Language Query Acceptance:**
- ✅ "on what date did we see most writing appointments booked in the Spring?" - ACCEPTED (original problem)
- ✅ "how many sessions were there in the Spring?" - ACCEPTED (original problem)
- ✅ "how many sessions in total?" - ACCEPTED (original problem)
- ✅ "what was the busiest day?" - ACCEPTED
- ✅ "how many students visited?" - ACCEPTED
- ✅ "when do we have the most appointments?" - ACCEPTED
- ✅ "show me the data for spring semester" - ACCEPTED
- ✅ "how many appointments this year?" - ACCEPTED
- ✅ "what are the overall trends?" - ACCEPTED

**Natural Language Query Test Results:**
- **Total Tests:** 9
- **Passed:** 9 (100.0%)
- **Failed:** 0 (0.0%)

## How It Works Together

1. **User asks:** "what is the average life expectancy of a hippo?"
2. **Layer 1 (Input Validation):** Blocked immediately - contains "hippo" and "life expectancy"
3. **Result:** User receives rejection message before LLM is even called

Even if a clever query bypasses Layer 1:
1. **Layer 2 (System Prompt):** LLM instructed to refuse off-topic questions
2. **Result:** LLM responds with refusal message

Even if LLM ignores Layer 2:
1. **Layer 3 (Response Filtering):** Response checked for generic knowledge patterns
2. **Result:** Off-topic response blocked and replaced with refusal message

## Files Modified

1. `src/ai_chat/prompt_templates.py` - Enhanced system prompts (balanced approach)
2. `src/ai_chat/safety_filters.py` - Strengthened validation and filtering (blocklist-only)
3. `test_jailbreak_protection.py` - NEW: Comprehensive test suite
4. `test_blocked_query_logging.py` - NEW: Logging functionality tests
5. `test_session_type_queries.py` - NEW: Session type comparison tests
6. `test_temporal_queries.py` - NEW: Temporal query tests (days, times, months)
7. `test_simplified_validation.py` - NEW: Simplified blocklist validation tests
8. `test_natural_language_queries.py` - NEW: Natural language query tests

## Usage

The improvements are automatic. No configuration changes needed. The system will now:

1. Block off-topic queries before reaching the LLM
2. Instruct the LLM to refuse off-topic questions
3. Catch and filter any off-topic responses that slip through
4. **Log all blocked queries to a file for review**

### Blocked Query Logging

All blocked queries are automatically logged to `logs/blocked_queries.log` for review.

**Log Format:**
```
[2026-01-20 23:05:17] BLOCKED - off_topic: hippo
Query: what is the average life expectancy of a hippo?
--------------------------------------------------------------------------------
```

**Configuration:**

By default, logging is enabled. To disable or customize:

```python
# Disable logging
validator = InputValidator(log_blocked_queries=False)

# Custom log file location
validator = InputValidator(log_file='custom/path/to/queries.log')
```

**Why Log Blocked Queries?**

- Monitor what users are trying to ask
- Identify patterns in blocked queries
- Improve filtering rules based on real usage
- Detect potential improvements to the system
- Understand user intent when queries are blocked

Run tests to verify:
```bash
# Test jailbreak protection
python test_jailbreak_protection.py

# Test logging functionality
python test_blocked_query_logging.py
```

## Future Enhancements (Optional)

If needed, consider:
1. Learning from blocked queries to expand keyword lists
2. Adding semantic similarity checking for better context understanding
3. Fine-tuning the model on refusal patterns
4. Adding user feedback loop to adjust strictness
