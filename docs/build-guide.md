# Writing Studio Analytics Tool - Build Guide Outline

**Project Goal:** Create a privacy-first, portable analytics tool for Writing Studio tutoring data that runs locally on university computers with no installation required.

**Target Users:** Graduate Assistants and Supervisors (non-technical, creative writing backgrounds)

**Key Requirements:**
- ✅ Data privacy (no PII sent to cloud)
- ✅ Works on locked-down university computers (no admin rights)
- ✅ Zero installation required
- ✅ Handles duplicate columns automatically
- ✅ Academic calendar awareness
- ✅ Auto-generates visualizations
- ✅ Handles multi-year CSVs
- ✅ Optional: Local AI for custom questions

---

## **BUILD STRATEGY**

**Phase 1 (Option B):** Core analytics + visualizations (no AI) - ~150MB package  
**Phase 2 (Option A):** Add local AI for Q&A - ~2.7GB package

---

## **PHASE 1: PROJECT SETUP & FOUNDATION**

### **1.1 Repository Setup**
- [X] Create GitHub repo: `writing-studio-analytics`
- [X] Initialize with README, .gitignore (Python), MIT license
- [X] Create branch structure (main, dev)
- [X] Set up project directory structure
- [X] Create initial commit

### **1.2 Directory Structure**
```
writing-studio-analytics/
├── src/
│   ├── core/                    # Core analysis modules
│   │   ├── __init__.py
│   │   ├── data_loader.py       # CSV loading & validation
│   │   ├── data_cleaner.py      # Duplicate removal, standardization
│   │   ├── privacy.py           # PII detection & anonymization
│   │   └── metrics.py           # KPI calculations
│   ├── visualizations/          # Chart generation
│   │   ├── __init__.py
│   │   ├── charts.py            # Individual chart functions
│   │   └── report_generator.py # PDF compilation
│   ├── utils/                   # Helper functions
│   │   ├── __init__.py
│   │   ├── academic_calendar.py # Semester detection
│   │   └── formatters.py        # Data formatting utilities
│   └── app.py                   # Main Streamlit app
├── prompts/                     # AI system prompts (Phase 2)
│   └── tutoring_expert.txt
├── tests/                       # Unit tests
│   ├── test_data_cleaner.py
│   ├── test_privacy.py
│   └── test_metrics.py
├── docs/                        # Documentation
│   ├── user_guide.md
│   ├── technical_docs.md
│   └── handoff_guide.md
├── examples/                    # Sample data
│   └── sample_anonymized.csv
├── requirements.txt             # Python dependencies
├── .gitignore
├── LICENSE
└── README.md
```

### **1.3 Development Environment**
- [X] Set up Python virtual environment
- [X] Install core dependencies:
  - pandas
  - streamlit
  - seaborn
  - matplotlib
  - numpy
  - reportlab (or fpdf for PDF generation)
- [X] Create requirements.txt
- [X] Test basic Streamlit "Hello World"
- [X] Verify environment works correctly

---

## **PHASE 2: CORE DATA PROCESSING (No AI - Option B)**

### **2.1 Data Privacy Module** (`src/core/privacy.py`)
- [ ] Build PII detection function
  - Detect columns: email, first_name, last_name, student_id, tutor_id
  - Pattern matching for email addresses
  - Name field detection
- [ ] Create anonymization logic
  - Hash-based anonymization for IDs
  - Remove PII columns entirely
  - Generate anonymized student/tutor identifiers
- [ ] Add data sanitization tests
- [ ] Document privacy guarantees (no data leaves machine)
- [ ] Create privacy audit log

### **2.2 Data Cleaning Module** (`src/core/data_cleaner.py`)
- [ ] Duplicate column detection algorithm
  - Compare column values for exact matches
  - Identify >95% similarity
  - Flag common duplicate patterns (Requested vs Scheduled)
- [ ] Column consolidation logic
  - Keep first occurrence, drop duplicates
  - Rename for clarity ("Requested Start At Date" → "Appointment Date")
  - Log what was removed
- [ ] Data type standardization
  - Parse dates correctly
  - Parse times correctly
  - Convert session length to float (hours)
- [ ] Handle missing values strategy
  - Identify critical vs non-critical columns
  - Imputation vs dropping logic
  - Document missing data patterns

### **2.3 Academic Calendar Parser** (`src/utils/academic_calendar.py`)
- [ ] Semester detection function
  - Spring: January - May
  - Summer: May - August
  - Fall: August - December
- [ ] Academic year grouping (e.g., "2023-2024")
- [ ] Week-of-semester calculator (Week 1-16)
- [ ] Peak period identifier
  - Midterms: Weeks 5-7
  - Finals: Weeks 12-14
- [ ] Intercession detection (Winter, Summer, Fall)

### **2.4 Metrics Engine** (`src/core/metrics.py`)
- [ ] Booking lead time calculator
  - Days/hours between booking and appointment
  - Percentile breakdowns
  - Same-day vs advance booking categories
- [ ] No-show rate analyzer
  - Overall no-show %
  - By day of week
  - By time of day
  - By semester
- [ ] Session length statistics
  - Average, median session length
  - Distribution analysis
- [ ] Student satisfaction aggregator
  - Pre/post confidence scores
  - Satisfaction ratings (1-7 scale)
  - Tutor rapport scores
  - Identify trends over time
- [ ] Tutor workload metrics
  - Sessions per tutor
  - Hours per tutor
  - Session type distribution
  - Workload balance analysis

---

## **PHASE 3: VISUALIZATION LAYER**

### **3.1 Chart Templates** (`src/visualizations/charts.py`)
- [ ] Design 8-10 standard chart types (seaborn/matplotlib)
- [ ] Establish color scheme/branding
  - University colors if applicable
  - Colorblind-safe palettes
- [ ] Set consistent styling (fonts, sizes, grid)
- [ ] Create reusable chart template functions

### **3.2 Auto-Generated Reports** (Individual Chart Functions)

**Chart 1: Booking Lead Time Distribution**
- [ ] Histogram of days in advance
- [ ] Overlay median/mean lines
- [ ] Category breakdown (same-day, 1-day, week+)

**Chart 2: Sessions by Semester (Multi-Year Comparison)**
- [ ] Bar chart: sessions per semester
- [ ] Year-over-year comparison
- [ ] Growth rate annotations

**Chart 3: No-Show Rates Analysis**
- [ ] Heatmap: day of week × time of day
- [ ] Trend line over time
- [ ] Comparison by semester

**Chart 4: Student Satisfaction Trends**
- [ ] Line chart: satisfaction scores over time
- [ ] Pre/post confidence comparison
- [ ] Rolling average overlay

**Chart 5: Session Topics Analysis**
- [ ] Word cloud from agenda fields
- [ ] Bar chart: top topics
- [ ] Topic trends over time

**Chart 6: Tutor Workload Distribution**
- [ ] Bar chart: sessions per tutor
- [ ] Box plot: workload variation
- [ ] Flag overworked/underutilized tutors

**Chart 7: Hourly Demand Heatmap**
- [ ] Heatmap: day × hour
- [ ] Identify peak times
- [ ] Capacity planning insights

**Chart 8: First-Time vs Returning Students**
- [ ] Pie chart: first-time %
- [ ] Retention rate calculation
- [ ] Trend over semesters

**Chart 9: Confidence Change Analysis**
- [ ] Before/after confidence scores
- [ ] Distribution of improvement
- [ ] Identify sessions with biggest impact

**Chart 10: Peak Usage Periods**
- [ ] Bar chart: sessions by week of semester
- [ ] Overlay midterm/finals weeks
- [ ] Multi-year comparison

### **3.3 Report Export** (`src/visualizations/report_generator.py`)
- [ ] Generate multi-page PDF report
  - Cover page with summary stats
  - All 10 charts with descriptions
  - Actionable insights section
  - Data quality notes
- [ ] Summary statistics page
  - Key metrics (total sessions, no-show %, avg satisfaction)
  - Year-over-year comparisons
  - Highlight concerning trends
- [ ] Actionable insights section
  - Auto-generated recommendations
  - Flag issues (high no-shows, low satisfaction)
  - Suggest operational improvements
- [ ] Export raw cleaned data option (CSV)
  - Anonymized version for further analysis
  - Include data dictionary

---

## **PHASE 4: STREAMLIT UI**

### **4.1 App Layout Design** (`src/app.py`)
- [ ] Privacy-first banner/messaging
  - "🔒 Your data never leaves this computer"
  - FERPA compliance statement
  - No cloud, no tracking
- [ ] File upload interface
  - Drag-and-drop CSV upload
  - File format validation
  - Example CSV download link
- [ ] Progress indicators
  - Loading spinner during processing
  - Step-by-step status updates
  - Estimated time remaining
- [ ] Report download section
  - PDF download button
  - Cleaned CSV download
  - Individual chart downloads

### **4.2 User Flow Implementation**
- [ ] Upload CSV → Validate format
  - Check for required columns
  - Verify date/time formats
  - Show warnings for missing data
- [ ] Show cleaning summary
  - "Removed X duplicate columns"
  - "Anonymized Y student records"
  - "Found Z data quality issues"
- [ ] Display all charts in organized tabs/sections
  - Tab 1: Overview & Key Metrics
  - Tab 2: Booking Behavior
  - Tab 3: Student Satisfaction
  - Tab 4: Tutor Analytics
  - Tab 5: Operational Insights
- [ ] Export buttons (PDF, cleaned CSV)

### **4.3 Error Handling**
- [ ] Invalid file format messages
  - User-friendly error descriptions
  - Suggestions for fixing
- [ ] Missing required columns detection
  - List which columns are missing
  - Show expected vs actual schema
- [ ] Helpful error messages
  - Avoid technical jargon
  - Provide actionable next steps
  - Link to documentation

### **4.4 Testing with Real Data**
- [ ] Test with Penji export data (anonymized)
- [ ] Test with multi-year data (2+ years)
- [ ] Test with edge cases
  - Missing columns
  - Weird date formats
  - Special characters in text fields
  - Empty/null values
  - Very large files (10k+ rows)
- [ ] Performance benchmarking
  - Load time for large CSVs
  - Chart generation speed
  - PDF export time

---

## **PHASE 5: LOCAL AI INTEGRATION (Option A Upgrade)**

### **5.1 AI Infrastructure Research**
- [ ] Test local model options
  - Phi-3 Mini (2.3GB, Microsoft)
  - Llama 3.2 (2-4GB, Meta)
  - TinyLlama (600MB, lightweight)
- [ ] Evaluate llama.cpp vs Ollama
  - Portability (llama.cpp = single exe)
  - Ease of use (Ollama = simpler API)
  - Performance benchmarks
- [ ] Test inference speed on typical queries
  - "What % of students book same-day?"
  - "Compare Spring 2024 vs Fall 2024"
  - Response time < 5 seconds target

### **5.2 Prompt Engineering** (`prompts/tutoring_expert.txt`)
- [ ] Write master system prompt
  - Tutoring expert persona
  - Understanding of academic environment
  - Focus on actionable insights
- [ ] Academic calendar context injection
  - Semester definitions
  - Peak periods knowledge
  - Academic vs calendar year awareness
- [ ] Data schema explanation
  - Column descriptions
  - Metric definitions
  - Common patterns in the data
- [ ] Few-shot examples for common questions
  - "What's the no-show rate?" → example answer
  - "When do students book?" → example answer
  - "Which tutors are busiest?" → example answer

### **5.3 Q&A Interface** (Add to `src/app.py`)
- [ ] Build chat interface in Streamlit
  - Chat input box
  - Message history display
  - Clear conversation button
- [ ] Connect to local model
  - llama.cpp subprocess integration OR
  - Ollama API connection (localhost:11434)
- [ ] Context management
  - Pass data summary to model
  - Include relevant metrics in context
  - Limit context window size
- [ ] Response formatting and citation
  - Format answers clearly
  - Cite specific data points
  - Show confidence levels

### **5.4 AI Features Implementation**
- [ ] Custom question answering
  - Natural language queries
  - Extract relevant data
  - Generate answer with citations
- [ ] Trend explanation
  - "Why did no-shows spike in March?"
  - Correlate with external factors
  - Suggest hypotheses
- [ ] Recommendation generation
  - Suggest operational improvements
  - Identify opportunities
  - Flag risks
- [ ] Comparative analysis queries
  - Semester-to-semester
  - Year-over-year
  - Before/after interventions

---

## **PHASE 6: PORTABLE PACKAGING**

### **6.1 Portable Python Setup**
- [ ] Download WinPython Portable (Python 3.11+)
- [ ] Test all dependencies in portable environment
  - Install pandas, streamlit, seaborn, etc.
  - Verify imports work
  - Test Streamlit launches
- [ ] Create minimal Python distribution
  - Remove unnecessary packages
  - Keep only required libraries
  - Compress to reduce size
- [ ] Document Python version used

### **6.2 Local AI Bundling** (Option A only)
- [ ] Download chosen model file
  - Phi-3 Mini (recommended) OR
  - Llama 3.2 3B
- [ ] Download llama.cpp executable
  - Windows: llama.exe
  - Mac: llama (if needed)
- [ ] Test model loading
  - Verify model runs
  - Test inference speed
  - Confirm response quality
- [ ] Optimize model settings
  - Context size
  - Temperature
  - Max tokens

### **6.3 Launch Scripts**

**Windows: `START_HERE.bat`**
- [ ] Create batch file
  - Set working directory
  - Launch Streamlit with portable Python
  - Auto-open browser
  - Keep console window for status
- [ ] Add error handling
  - Check if Python exists
  - Check if port is available
  - Show helpful error messages
- [ ] Test on clean Windows machine

**Mac/Linux: `start.sh`** (if needed)
- [ ] Create shell script
  - Similar functionality to .bat
  - Set executable permissions
  - Test on Mac/Linux

### **6.4 Package Assembly**

**Option B Structure (No AI - ~150MB):**
```
WritingStudioAnalyzer_v1.0/
├── START_HERE.bat              # Launch script
├── README.txt                   # Simple 1-page instructions
├── python/                      # WinPython portable (~150MB)
│   ├── python.exe
│   └── Lib/ (all dependencies)
├── app/                         # Your application code
│   ├── src/
│   ├── requirements.txt
│   └── app.py
└── examples/                    # Sample files
    ├── sample_data.csv
    └── sample_output.pdf
```

**Option A Structure (With AI - ~2.7GB):**
```
WritingStudioAnalyzer_v1.0/
├── START_HERE.bat
├── README.txt
├── python/ (~150MB)
├── app/
├── ai_model/                    # Local AI components
│   ├── llama.cpp/
│   │   └── llama.exe
│   └── models/
│       └── phi-3-mini.gguf (~2.5GB)
└── examples/
```

### **6.5 Testing on Clean Machine**
- [ ] Test on computer without Python installed
  - Fresh Windows VM or friend's laptop
  - Verify zero dependencies needed
- [ ] Test on locked-down university computer
  - No admin rights
  - Limited network access
  - Restricted file permissions
- [ ] Document any issues/workarounds
  - Antivirus warnings
  - Firewall prompts
  - Port conflicts
- [ ] Create troubleshooting guide

---

## **PHASE 7: DOCUMENTATION**

### **7.1 User Documentation** (`docs/user_guide.md`)
- [ ] Quick start guide (1-page, with screenshots)
  - Step 1: Extract ZIP
  - Step 2: Double-click START_HERE.bat
  - Step 3: Upload CSV
  - Step 4: Download report
- [ ] FAQ section
  - "What data is required?"
  - "Where does my data go?" (Nowhere - local only)
  - "How do I interpret the charts?"
  - "What if I get an error?"
- [ ] Troubleshooting common issues
  - "Browser doesn't open" → Manual navigation
  - "Port already in use" → Close other apps
  - "File upload fails" → Check file format
- [ ] Chart interpretation guide
  - What each chart shows
  - How to read the data
  - What actions to take based on trends

### **7.2 Technical Documentation** (`docs/technical_docs.md`)
- [ ] Code architecture overview
  - Module descriptions
  - Data flow diagram
  - Key design decisions
- [ ] How to add new charts
  - Chart template structure
  - Adding to report generator
  - Testing new visualizations
- [ ] How to update AI prompts (Option A)
  - Where prompts are stored
  - Prompt engineering best practices
  - Testing prompt changes
- [ ] How to refresh Python/dependencies
  - Updating WinPython
  - Upgrading libraries
  - Testing compatibility

### **7.3 Handoff Documentation** (`docs/handoff_guide.md`)
- [ ] File locations on shared drive
  - Latest version path
  - Backup locations
  - Archive of old versions
- [ ] How to modify/extend
  - Common customization requests
  - Code structure walkthrough
  - Testing procedures
- [ ] GitHub repository access
  - Repo URL
  - How to clone/pull updates
  - Branch strategy
- [ ] Contact information
  - Your email (for next 6 months)
  - Supervisor contact
  - IT support if needed

---

## **PHASE 8: VALIDATION & REFINEMENT**

### **8.1 Internal Testing**
- [ ] Run on 2-3 years of real Writing Studio data
  - Full dataset processing
  - Generate complete reports
  - Verify all charts render
- [ ] Verify all metrics make sense
  - Cross-check calculations manually
  - Confirm no-show rates are reasonable
  - Validate satisfaction trends
- [ ] Check charts are readable/useful
  - Legible labels
  - Appropriate scale/axes
  - Colorblind-accessible
- [ ] Test AI answers accuracy (Option A)
  - Ask 20+ questions
  - Verify answers against actual data
  - Ensure no hallucinations

### **8.2 Stakeholder Review**
- [ ] Demo to supervisor
  - 30-minute walkthrough
  - Show all features
  - Get feedback
- [ ] Get feedback from current GA
  - What questions do they want answered?
  - What charts are most useful?
  - What's confusing?
- [ ] Ask: "What questions aren't being answered?"
  - Missing metrics
  - Desired comparisons
  - Additional visualizations
- [ ] Collect feature requests
  - Prioritize based on value/effort
  - Document for future iterations

### **8.3 Refinement**
- [ ] Add requested features
  - Top 3-5 priority items
  - Quick wins first
- [ ] Fix bugs
  - Address all critical issues
  - Document known minor issues
- [ ] Improve chart clarity
  - Better labels
  - More context
  - Clearer insights
- [ ] Polish UI/UX
  - Smoother interactions
  - Better error messages
  - Loading indicators

---

## **PHASE 9: DEPLOYMENT & HANDOFF**

### **9.1 Final Package Creation**
- [ ] Create Option B ZIP (no AI - ~150MB)
  - Test complete package
  - Verify size
  - Create checksums
- [ ] Create Option A ZIP (with AI - ~2.7GB)
  - Test complete package
  - Verify AI works
  - Create checksums
- [ ] Upload to university shared drive
  - Get permanent link
  - Set permissions (view/download only)
  - Create shortcut for easy access
- [ ] Create backup copies
  - OneDrive/Google Drive backup
  - GitHub release
  - USB drive for supervisor

### **9.2 Training Session**
- [ ] Schedule 30-45 min demo
  - Supervisor + incoming GA
  - Book conference room with projector
  - Send calendar invite with agenda
- [ ] Walk through complete workflow
  1. Download/extract package
  2. Launch application
  3. Upload CSV
  4. Review each report section
  5. (Option A) Ask AI questions
  6. Export PDF report
- [ ] Hands-on practice
  - Let them try uploading data
  - Let them ask questions
  - Troubleshoot any issues
- [ ] Q&A session
  - Answer all questions
  - Document new questions for FAQ
- [ ] Record video tutorial (optional)
  - Screen recording of full workflow
  - 10-15 minute walkthrough
  - Upload to shared drive

### **9.3 Support Plan**
- [ ] Create shared doc for bug reports/feature requests
  - Google Doc or GitHub Issues
  - Template for reporting issues
  - Response time expectations
- [ ] Set up communication channel
  - Email address for questions
  - Slack channel (if available)
  - Office hours for first month
- [ ] Offer transition support
  - Available for troubleshooting first semester
  - Monthly check-ins (first 3 months)
  - Emergency contact for critical issues

---

## **PHASE 10: SEND TO BOSS**

### **10.1 Professional Presentation**
- [ ] Create 1-page executive summary
  - Problem: Manual data analysis is time-consuming
  - Solution: Automated, privacy-first analytics tool
  - Impact: Save X hours per semester, better insights
  - Sustainability: Zero ongoing costs, easy to maintain
- [ ] Highlight key features
  - Privacy-first (FERPA compliant)
  - Turnkey solution (no technical skills needed)
  - Cost savings (vs manual analysis or cloud tools)
  - Future-proof (well-documented, maintainable)
- [ ] Include sample outputs
  - PDF report from real data (anonymized)
  - Screenshots of key charts
  - Sample AI Q&A (if Option A)
- [ ] Mention GitHub repo
  - Institutional knowledge preservation
  - Future enhancements possible
  - Open for other departments

### **10.2 Demo Meeting**
- [ ] Schedule formal presentation
  - 45-60 minutes
  - Include decision-makers
  - Prepare slides (5-10 slides max)
- [ ] Live demo with real data
  - Use actual Writing Studio data (anonymized)
  - Show end-to-end workflow
  - Demonstrate key insights discovered
- [ ] Before/after comparison
  - Old way: Manual Excel analysis (hours)
  - New way: Automated reports (5 minutes)
  - Quality improvement: More comprehensive insights
- [ ] Emphasize ease of use
  - Non-technical users can operate
  - No training burden
  - Minimal maintenance
- [ ] Discuss long-term maintenance
  - Who will maintain (minimal effort needed)
  - Update schedule (annual dependency updates)
  - Support plan (documentation + your availability)

### **10.3 Portfolio Documentation**
- [ ] Write blog post (Medium/personal site)
  - Technical breakdown
  - Design decisions
  - Lessons learned
  - Impact achieved
- [ ] Update resume/LinkedIn
  - Project description
  - Technologies used
  - Measurable impact
- [ ] Polish GitHub README
  - Professional presentation
  - Clear documentation
  - Screenshots/demos
  - Installation instructions
- [ ] Create case study for job applications
  - Problem statement
  - Technical approach
  - Results achieved
  - Skills demonstrated

---

## **PHASE 11: POST-GRADUATION LEGACY**

### **11.1 Maintenance Handoff**
- [ ] Ensure GitHub access for Writing Studio
  - Transfer repo ownership OR
  - Add supervisor as admin
- [ ] Leave detailed contact info
  - Personal email (for critical bugs)
  - LinkedIn profile
  - Availability window (next 6-12 months)
- [ ] Document how to find help
  - Python community resources
  - Streamlit documentation
  - AI model documentation
  - Stack Overflow tags

### **11.2 Future Enhancement Ideas**
- [ ] Predictive analytics
  - Forecast busy weeks
  - Predict no-show likelihood
  - Capacity planning recommendations
- [ ] Automated email reports
  - Weekly summary emails
  - Semester wrap-up reports
  - Alert for concerning trends
- [ ] Penji API integration
  - Direct data pull (no CSV upload)
  - Real-time dashboard
  - Automated scheduled reports
- [ ] Multi-campus expansion
  - Comparative analytics across campuses
  - Best practices sharing
  - Benchmarking

---

## **SUCCESS METRICS**

**Usability:**
- ✅ GA can go from CSV to full report in <5 minutes
- ✅ Zero technical support requests in first month
- ✅ Non-technical users successfully operate tool

**Privacy:**
- ✅ No PII ever leaves the computer
- ✅ FERPA compliance verified
- ✅ No internet connection required (except install)

**Technical:**
- ✅ Handles 5+ years of data (20k+ rows)
- ✅ Generates all charts in <30 seconds
- ✅ PDF export works on first try

**Sustainability:**
- ✅ Tool still works in 3+ years with minimal maintenance
- ✅ Next GA can understand and modify code
- ✅ Documentation is clear and comprehensive

**Impact:**
- ✅ Supervisor says "This is awesome, thank you!"
- ✅ Tool is used regularly (at least monthly)
- ✅ Insights lead to operational improvements

---

## **TIMELINE ESTIMATE**

**Option B (No AI):**
- Phase 1-4: 2-3 weeks (core functionality)
- Phase 7-10: 1 week (documentation & handoff)
- **Total: 3-4 weeks**

**Option A (With AI):**
- Phase 1-4: 2-3 weeks
- Phase 5: 1-2 weeks (AI integration)
- Phase 6: 1 week (packaging with AI)
- Phase 7-10: 1 week
- **Total: 5-7 weeks**

---

## **NEXT STEPS**

1. ✅ Review this build guide
2. ✅ Confirm approach with supervisor (optional)
3. ⬜ Set up development environment
4. ⬜ Start Phase 1: Project Setup
5. ⬜ Begin building!

---

**Notes:**
- This is a living document - update as you progress
- Check off items as completed
- Add notes/lessons learned
- Adjust timeline based on actual progress
- Don't be afraid to iterate on the plan

**Good luck, Zachary! This is going to be an awesome legacy project. 🚀**
