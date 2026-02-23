================================================================================
              WRITING STUDIO ANALYTICS - USB PACKAGE
================================================================================

QUICK START (Recommended)
-------------------------
1. Double-click START_PROGRAM.bat
2. If prompted, allow first-time setup:
   - setup_portable_python.bat
   - INSTALL_DEPENDENCIES.bat
3. The application window will appear


WHAT'S IN THIS FOLDER
---------------------
START_PROGRAM.bat          - Main launcher (use this!)

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
A: First launch can take several minutes while Python and dependencies
   install. Keep the window open and follow prompts.

Q: "Application not found" error
A: Ensure these files are present in the same folder:
   START_PROGRAM.bat, RUN_WITH_PYTHON.bat, setup_portable_python.bat

Q: AI Chat tab shows "Model not found"
A: Ensure the models/ folder contains gemma-3-4b-it-q4_0.gguf


SYSTEM REQUIREMENTS
-------------------
- Windows 10 or later
- 8GB RAM minimum (16GB recommended)
- Internet required for first-time Python/dependency setup
- No internet required after setup is complete


DATA PRIVACY
------------
- All data stays on this computer
- No cloud services used
- FERPA compliant
- Audit logs saved to:
  %LOCALAPPDATA%\WritingStudioAnalytics\audit.log


FOR MORE HELP
-------------
See docs/USB_TRANSFER_INSTRUCTIONS.md for transfer instructions.
See docs/FINAL_HANDOFF_CHECKLIST.md for feature overview.


CONTACT
-------
For technical issues, contact the previous developer.
For data questions, contact the Writing Studio supervisor.

================================================================================
                    University of Arkansas Writing Studio
================================================================================
