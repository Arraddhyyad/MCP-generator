# MCP Gmail Integration

A FastAPI-powered Gmail assistant that automates HR email processing. 
It reads job-related emails, interprets job requirements, matches candidates, generates 
tailored resumes and cover letters, and sends replies—all in one workflow.

---

## Features
Gmail API Integration: Connects directly to Gmail using OAuth2.
Email Interpretation: Extracts job details (title, required skills, request type).
Profile Retrieval: Loads user profiles (education, experience, skills).
Candidate Matching: Finds the best candidate based on semantic matching.
Resume Builder: Generates polished, job-specific PDF resumes.
Cover Letter Writer: Creates customized cover letters.
Reply Email Automation: Composes and sends professional replies with attachments.
Web Dashboard: Manage emails, candidate matching, and replies at `http://localhost:8000`.

---

## Workflow Overview

1. Read Emails: Authenticate with Gmail; fetch recent HR-related emails.
2. Interpret Emails: Extract job title, skills, and request type using the Email Interpreter and stores it in
json format.
3. Retrieve Profiles: Load candidate profiles from `/profiles/{user_id}.json`.
4. Match Candidates (if requested): Rank candidates by computing similarity scores between job requirements and each profile.
5. Generate Documents: Build tailored resumes and cover letters highlighting relevant skills 
based on user profile and provided html template.
6. Compose Replies: Create email replies with attachments.
7. Send Replies: Dispatch professional replies directly through Gmail.
8. Dashboard: Monitor HR emails and trigger actions via a web UI.

---

## Project Structure

.
├── main.py                # FastAPI entry point
├── mcp_modules/           # MCP tools: email interpreter, matcher, builder, etc.
├── profiles/              # User profiles (JSON)
├── outputs/               # Generated resumes & cover letters
├── credentials.json       # Gmail API OAuth credentials
├── token.json             # Auto-generated Gmail OAuth token
└── README.md
```
---

## Setup & Installation

1. Clone Repo:

   ```bash
   git clone https://github.com/arraddhyyad/mcp-server.git
   cd mcp-gmail-integration
   ```
2. Install Dependencies:

   ```bash
   pip install -r requirements.txt
   ```
3. Install `wkhtmltopdf` (for PDF generation):

   * macOS: `brew install wkhtmltopdf`
   * Ubuntu: `sudo apt-get install wkhtmltopdf`
   * Windows: [Download here](https://wkhtmltopdf.org/)
4. Gmail API Setup:

   * Enable Gmail API in Google Cloud Console.
   * Download `credentials.json` and place it in the root.
5. Run App:

   ```bash
   python main.py
   ```
6. Access Dashboard:
   Visit [http://localhost:8000](http://localhost:8000).

---

## How It Works

Step 1: Emails fetched from Gmail.
Step 2: Parsed by Email Interpreter.
Step 3: Candidate Matcher picks best profile (if requested).
Step 4: Profile Retriever loads user details.
Step 5: Resume Builder and Cover Letter Writer generate tailored documents.
Step 6: Reply Email Generator drafts a professional response.
Step 7: Gmail Sender replies with documents attached.
Step 8: Web UI provides an interactive management dashboard.

---

## Notes

Token Refresh: `token.json` should be refreshed periodically.
Fallback: Resumes are saved as `.html` if PDF generation fails.
Customization: Edit `resume_builder.py` to modify resume templates.
