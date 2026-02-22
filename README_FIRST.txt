================================================================================
              WRITING STUDIO ANALYTICS - USB PACKAGE
================================================================================

QUICK START (Recommended)
-------------------------
1. Double-click START_PROGRAM.bat
2. Wait 10-30 seconds for first launch
3. The application window will appear

That's it! The executable includes everything needed.


ALTERNATIVE: Run with Python (For Developers)
----------------------------------------------
If you need to modify the code or the executable doesn't work:

1. Double-click setup_portable_python.bat
   - Downloads Python (~15MB)
   - Takes 2-5 minutes

2. Double-click INSTALL_DEPENDENCIES.bat
   - Installs required packages (~500MB)
   - Takes 5-15 minutes

3. Double-click RUN_WITH_PYTHON.bat
   - Runs from source code


WHAT'S IN THIS FOLDER
---------------------
START_PROGRAM.bat          - Main launcher (use this!)
WritingStudioAnalytics.exe - The compiled application (~3.5GB)

setup_portable_python.bat  - Downloads portable Python
INSTALL_DEPENDENCIES.bat   - Installs Python packages
RUN_WITH_PYTHON.bat        - Runs from source code

SOURCE_CODE/               - Full source code for future development
docs/                      - Documentation and guides
models/                    - AI model for chat feature
courses.csv                - Course data file (required)


FEATURES
--------
- Scheduled session analytics
- Walk-in session analytics
- FERPA-compliant anonymization
- PDF report generation
- AI Chat for asking questions about your data (local, no cloud)


TROUBLESHOOTING
---------------
Q: Nothing happens when I run START_PROGRAM.bat
A: Wait 30 seconds. First launch unpacks files. Check that 
   WritingStudioAnalytics.exe exists in this folder.

Q: "Application not found" error
A: Ensure WritingStudioAnalytics.exe is in the same folder as 
   START_PROGRAM.bat

Q: Antivirus warning
A: This is a false positive. The executable is safe. Add an exception 
   or use the Python method instead.

Q: AI Chat tab shows "Model not found"
A: Ensure the models/ folder contains gemma-3-4b-it-q4_0.gguf


SYSTEM REQUIREMENTS
-------------------
- Windows 10 or later
- 8GB RAM minimum (16GB recommended)
- No installation required
- No internet connection required (after initial setup)


DATA PRIVACY
------------
- All data stays on this computer
- No cloud services used
- FERPA compliant
- Audit logs saved to:
  %LOCALAPPDATA%\WritingStudioAnalytics\audit.log


FOR MORE HELP
-------------
See docs/SUPERVISOR_HANDOFF_V2.md for detailed instructions.
See docs/FINAL_HANDOFF_CHECKLIST.md for feature overview.


CONTACT
-------
For technical issues, contact the previous developer.
For data questions, contact the Writing Studio supervisor.

================================================================================
                    University of Arkansas Writing Studio
================================================================================