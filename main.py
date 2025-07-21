from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from typing import Any, Dict, List
import uvicorn
import json
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
from mcp_modules.email_interpreter import EmailInterpreter 
from mcp_modules.gmail_sender import send_email_with_attachments
from mcp_modules.candidate_matcher import CandidateMatcher

# Gmail API setup
SCOPES = ['https://www.googleapis.com/auth/gmail.send',
          'https://www.googleapis.com/auth/gmail.readonly']

# Import MCP tools
try:
    from mcp_modules.cover_letter_writer import cover_letter_writer
    from mcp_modules.profile_retriever import profile_retriever
    from mcp_modules.resume_builder import resume_builder
    from mcp_modules.reply_email_generator import reply_email_generator
    print("✓ All MCP modules imported successfully")
except ImportError as e:
    print(f"Import error: {e}")
    # Dummy functions for testing
    def cover_letter_writer(context): 
        return {"status": "success", "output": {"cover_letter_path": "outputs/sample_cover.pdf"}}
    
    def profile_retriever(context): 
        return {"status": "success", "output": {"user_profile": {"name": "John Doe"}}}
    
    def resume_builder(context): 
        return {"status": "success", "output": {"resume_path": "outputs/sample_resume.pdf"}}
    
    def reply_email_generator(context): 
        return {"status": "success", "output": {"email_body": "Sample reply"}}

app = FastAPI(title="MCP Gmail Integration")

class GmailService:
    def __init__(self):
        self.service = None
        self.user_email = None
        self.authenticate()
    
    def authenticate(self):
        creds = None
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open("token.json", "w") as token:
                token.write(creds.to_json())
        
        try:
            self.service = build("gmail", "v1", credentials=creds)
            profile = self.service.users().getProfile(userId="me").execute()
            self.user_email = profile.get("emailAddress", "Unknown")
        except HttpError as error:
            print(f"Gmail auth error: {error}")
    
    def get_recent_hr_emails(self, max_results=5):
        try:
            query = "from:hr OR from:recruiter OR from:hiring OR subject:job OR subject:interview OR subject:position"
            results = self.service.users().messages().list(userId="me", q=query,labelIds=["INBOX"], maxResults=max_results).execute()
            messages = results.get("messages", [])
            
            hr_emails = []
            for msg in messages:
                msg_data = self.service.users().messages().get(userId="me", id=msg["id"]).execute()
                headers = msg_data["payload"].get("headers", [])
                
                subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
                sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown")
                date = next((h["value"] for h in headers if h["name"] == "Date"), "Unknown")
                
                body = self.extract_email_body(msg_data["payload"])
                
                hr_emails.append({
                    "id": msg["id"],
                    "subject": subject,
                    "sender": sender,
                    "date": date,
                    "body": body
                })
            
            return hr_emails
        except HttpError as error:
            print(f"Error fetching emails: {error}")
            return []
    
    def extract_email_body(self, payload):
        body = ""
        if "parts" in payload:
            for part in payload["parts"]:
                if part["mimeType"] == "text/plain" and "data" in part["body"]:
                    body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
                    break
        elif payload["mimeType"] == "text/plain" and "data" in payload["body"]:
            body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")
        return body

# Initialize services
gmail_service = GmailService()
email_interpreter = EmailInterpreter()
candidate_matcher = CandidateMatcher()

# Simple HTML template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCP Gmail Integration</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; background: #f0f0f0; padding: 20px; margin-bottom: 20px; }
        .section { background: white; padding: 20px; margin-bottom: 20px; border: 1px solid #ddd; }
        .email-card { background: #f9f9f9; padding: 15px; margin-bottom: 10px; border-left: 4px solid #007bff; }
        .email-header { font-weight: bold; margin-bottom: 10px; }
        .email-body { font-size: 14px; color: #666; margin-top: 10px; max-height: 100px; overflow-y: auto; }
        .btn { background: #007bff; color: white; padding: 10px 20px; border: none; cursor: pointer; margin: 5px; }
        .btn:hover { background: #0056b3; }
        .btn:disabled { background: #ccc; cursor: not-allowed; }
        .btn.success { background: #28a745; }
        .hidden { display: none; }
        .result { background: #e9ecef; padding: 15px; margin: 10px 0; border-left: 4px solid #28a745; }
        .error { border-left-color: #dc3545; background: #f8d7da; }
        .processing { border-left-color: #ffc107; background: #fff3cd; }
        .candidate-card { background: #f8f9fa; padding: 15px; margin: 10px 0; border-left: 4px solid #28a745; }
        .candidate-score { font-weight: bold; color: #28a745; }
        .score-breakdown { font-size: 12px; color: #666; margin-top: 5px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 MCP Gmail Integration</h1>
        <p>Connected: {{ user_email }}</p>
    </div>

    <div class="section">
        <h3>📬 Recent HR Emails</h3>
        <div id="hrEmails">
            {{ hr_emails_html }}
        </div>
    </div>

    <div class="section">
        <h3>💬 Email Response Assistant</h3>
        <button class="btn" onclick="showEmailSelection()">Help Me Respond</button>
        <button class="btn success" onclick="showCandidateMatching()">Find Best Candidate</button>
        
        <div id="emailSelection" class="hidden">
            <h4>Select emails to respond to:</h4>
            <div id="emailList"></div>
            <button class="btn" onclick="processEmails()">Process Selected Emails</button>
        </div>
        
        <div id="candidateMatching" class="hidden">
            <h4>Select emails to find best candidates for:</h4>
            <div id="candidateEmailList"></div>
            <button class="btn success" onclick="processCandidateMatching()">Find Best Candidates</button>
        </div>
        
        <div id="results"></div>
    </div>

    <script>
        let hrEmails = {{ hr_emails_json }};
        
        function showEmailSelection() {
            document.getElementById('emailSelection').classList.remove('hidden');
            document.getElementById('candidateMatching').classList.add('hidden');
            
            const emailList = document.getElementById('emailList');
            emailList.innerHTML = '';
            
            if (hrEmails.length === 0) {
                emailList.innerHTML = '<p>No HR emails found.</p>';
                return;
            }
            
            hrEmails.forEach((email, index) => {
                const div = document.createElement('div');
                div.innerHTML = `
                    <label style="display: block; margin: 10px 0;">
                        <input type="checkbox" value="${index}" style="margin-right: 10px;">
                        <strong>${email.subject}</strong> - ${email.sender}
                    </label>
                `;
                emailList.appendChild(div);
            });
        }
        
        function showCandidateMatching() {
            document.getElementById('candidateMatching').classList.remove('hidden');
            document.getElementById('emailSelection').classList.add('hidden');
            
            const candidateEmailList = document.getElementById('candidateEmailList');
            candidateEmailList.innerHTML = '';
            
            if (hrEmails.length === 0) {
                candidateEmailList.innerHTML = '<p>No HR emails found.</p>';
                return;
            }
            
            hrEmails.forEach((email, index) => {
                const div = document.createElement('div');
                div.innerHTML = `
                    <label style="display: block; margin: 10px 0;">
                        <input type="checkbox" value="${index}" style="margin-right: 10px;">
                        <strong>${email.subject}</strong> - ${email.sender}
                    </label>
                `;
                candidateEmailList.appendChild(div);
            });
        }
        
        async function processEmails() {
            const checkboxes = document.querySelectorAll('#emailList input[type="checkbox"]:checked');
            
            if (checkboxes.length === 0) {
                alert('Please select at least one email.');
                return;
            }
            
            const button = document.querySelector('button[onclick="processEmails()"]');
            button.disabled = true;
            button.textContent = 'Processing...';
            
            const results = document.getElementById('results');
            results.innerHTML = '<h4>Processing Results:</h4>';
            
            for (let checkbox of checkboxes) {
                const emailIndex = checkbox.value;
                const email = hrEmails[emailIndex];
                
                const resultDiv = document.createElement('div');
                resultDiv.className = 'result processing';
                resultDiv.innerHTML = `<h5>📧 ${email.subject}</h5><p>🔄 Processing...</p>`;
                results.appendChild(resultDiv);
                
                try {
                    await processEmailChain(email, resultDiv);
                } catch (error) {
                    resultDiv.className = 'result error';
                    resultDiv.innerHTML += `<p>❌ Error: ${error.message}</p>`;
                }
            }
            
            button.disabled = false;
            button.textContent = 'Process Selected Emails';
        }
        
        async function processCandidateMatching() {
            const checkboxes = document.querySelectorAll('#candidateEmailList input[type="checkbox"]:checked');
            
            if (checkboxes.length === 0) {
                alert('Please select at least one email.');
                return;
            }
            
            const button = document.querySelector('button[onclick="processCandidateMatching()"]');
            button.disabled = true;
            button.textContent = 'Finding Candidates...';
            
            const results = document.getElementById('results');
            results.innerHTML = '<h4>Candidate Matching Results:</h4>';
            
            for (let checkbox of checkboxes) {
                const emailIndex = checkbox.value;
                const email = hrEmails[emailIndex];
                
                const resultDiv = document.createElement('div');
                resultDiv.className = 'result processing';
                resultDiv.innerHTML = `<h5>🔍 ${email.subject}</h5><p>🔄 Finding best candidate...</p>`;
                results.appendChild(resultDiv);
                
                try {
                    await processCandidateMatchingChain(email, resultDiv);
                } catch (error) {
                    resultDiv.className = 'result error';
                    resultDiv.innerHTML += `<p>❌ Error: ${error.message}</p>`;
                }
            }
            
            button.disabled = false;
            button.textContent = 'Find Best Candidates';
        }
        
        async function processEmailChain(email, resultDiv) {
            try {
                // Interpret email and get user info
                const interpretation = await callAPI('/tools/email_interpreter', {
                    input: { email_text: email.body }
                });
                
                const userId = interpretation.output?.job_info?.user_id || 'default_user';
                
                // Check if this is a candidate matching request
                if (interpretation.output?.job_info?.request_type === 'find_best_candidate') {
                    await processCandidateMatchingChain(email, resultDiv);
                    return;
                }
                
                // Process normal user-specific request
                await processUserRequest(userId, interpretation, resultDiv, email);
                
            } catch (error) {
                throw error;
            }
        }
        
        async function processUserRequest(userId, interpretation, resultDiv, email) {
            try {
                resultDiv.innerHTML += `<p>✅ Processing for user: ${userId}</p>`;
                
                // Get profile
                const profile = await callAPI('/tools/profile_retriever', {
                    input: { user_id: userId }
                });
                
                // Build resume
                const resume = await callAPI('/tools/resume_builder', {
                    input: { user_id: userId },
                    output: { user_profile: profile.output.user_profile, job_info: interpretation.output.job_info }
                });
                
                // Write cover letter
                const coverLetter = await callAPI('/tools/cover_letter_writer', {
                    input: { user_id: userId },
                    output: { user_profile: profile.output.user_profile, job_info: interpretation.output.job_info }
                });
                
                // Generate reply
                const reply = await callAPI('/tools/reply_email_generator', {
                    input: { user_id: userId },
                    output: {
                        user_profile: profile.output.user_profile,
                        job_info: interpretation.output.job_info,
                        resume_path: resume.output.resume_path,
                        cover_letter_path: coverLetter.output.cover_letter_path
                    }
                });
                
                // Send email
                await callAPI('/tools/send_reply_email', {
                    input: { user_id: userId, to_email: email.sender },
                    output: {
                        email_subject: `Re: ${email.subject}`,
                        email_body: reply.output.email_body,
                        resume_path: resume.output.resume_path,
                        cover_letter_path: coverLetter.output.cover_letter_path
                    }
                });
                
                resultDiv.className = 'result';
                resultDiv.innerHTML += '<p>✅ Email sent successfully!</p>';
                
            } catch (error) {
                throw error;
            }
        }
        
        async function processCandidateMatchingChain(email, resultDiv) {
            try {
                // Find best candidate
                const matchingResult = await callAPI('/tools/candidate_matcher', {
                    input: { email_text: email.body }
                });
                
                if (matchingResult.status === 'error') {
                    resultDiv.className = 'result error';
                    resultDiv.innerHTML += `<p>❌ ${matchingResult.message}</p>`;
                    return;
                }
                
                const bestCandidate = matchingResult.best_candidate;
                
                // Display candidate info
                const candidateInfo = `
                    <div class="candidate-card">
                        <h5>🏆 Best Candidate: ${bestCandidate.name}</h5>
                        <p><strong>Email:</strong> ${bestCandidate.email}</p>
                        <p class="candidate-score">Match Score: ${bestCandidate.breakdown.overall_match}</p>
                        <div class="score-breakdown">
                            Skills: ${bestCandidate.breakdown.skills_match} | 
                            Experience: ${bestCandidate.breakdown.experience_match} | 
                            Education: ${bestCandidate.breakdown.education_match}
                        </div>
                    </div>
                `;
                resultDiv.innerHTML += candidateInfo;
                
                // Process application for best candidate
                const interpretation = { output: { job_info: matchingResult.job_requirements } };
                await processUserRequest(bestCandidate.user_id, interpretation, resultDiv, email);
                
            } catch (error) {
                throw error;
            }
        }
        
        async function callAPI(endpoint, data) {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            if (result.error) {
                throw new Error(result.error);
            }
            
            return result;
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def read_root():
    hr_emails = gmail_service.get_recent_hr_emails()
    
    hr_emails_html = ""
    for email in hr_emails:
        hr_emails_html += f"""
        <div class="email-card">
            <div class="email-header">{email['subject']}</div>
            <div>From: {email['sender']}</div>
            <div>Date: {email['date']}</div>
            <div class="email-body">{email['body'][:200]}{'...' if len(email['body']) > 200 else ''}</div>
        </div>
        """
    
    return HTML_TEMPLATE.replace("{{ user_email }}", gmail_service.user_email or "Not connected") \
                       .replace("{{ hr_emails_html }}", hr_emails_html) \
                       .replace("{{ hr_emails_json }}", json.dumps(hr_emails))

@app.post("/tools/email_interpreter")
def email_interpreter_endpoint(context: Dict[str, Any]):
    try:
        email_text = context["input"]["email_text"]
        job_info = email_interpreter.interpret_email(email_text)
        return {"output": {"job_info": job_info}}
    except Exception as e:
        return {"error": str(e), "status": "error"}

@app.post("/tools/candidate_matcher")
def candidate_matcher_endpoint(context: Dict[str, Any]):
    try:
        email_text = context["input"]["email_text"]
        result = candidate_matcher.find_best_candidate(email_text)
        return result
    except Exception as e:
        return {"error": str(e), "status": "error"}

@app.post("/tools/profile_retriever")
def profile_retriever_endpoint(context: Dict[str, Any]):
    try:
        if "input" not in context:
            context["input"] = {}
        if "user_id" not in context["input"]:
            context["input"]["user_id"] = "default_user"
        return profile_retriever(context)
    except Exception as e:
        return {"error": str(e), "status": "error"}

@app.post("/tools/resume_builder")
def resume_builder_endpoint(context: Dict[str, Any]):
    try:
        if "input" not in context:
            context["input"] = {}
        if "user_id" not in context["input"]:
            context["input"]["user_id"] = "default_user"
        return resume_builder(context)
    except Exception as e:
        return {"error": str(e), "status": "error"}

@app.post("/tools/cover_letter_writer")
def cover_letter_endpoint(context: Dict[str, Any]):
    try:
        if "input" not in context:
            context["input"] = {}
        if "user_id" not in context["input"]:
            context["input"]["user_id"] = "default_user"
        return cover_letter_writer(context)
    except Exception as e:
        return {"error": str(e), "status": "error"}

@app.post("/tools/reply_email_generator")
def reply_email_generator_endpoint(context: Dict[str, Any]):
    try:
        if "input" not in context:
            context["input"] = {}
        if "user_id" not in context["input"]:
            context["input"]["user_id"] = "default_user"
        return reply_email_generator(context)
    except Exception as e:
        return {"error": str(e), "status": "error"}

@app.post("/tools/send_reply_email")
def send_reply_email_endpoint(context: Dict[str, Any]):
    try:
        output = context.get("output", {})
        to_email = context.get("input", {}).get("to_email", "hr@example.com")

        send_result = send_email_with_attachments(
            to_email=to_email,
            subject=output["email_subject"],
            body=output["email_body"],
            attachments=[output["resume_path"], output["cover_letter_path"]]
        )

        return {"status": "success", "message_id": send_result.get("id", "N/A")}
    except Exception as e:
        return {"error": str(e), "status": "error"}

if __name__ == "__main__":
    print("🚀 Starting MCP Gmail Integration Server...")
    print("✓ Gmail API integrated")
    print("✓ MCP tools available")
    print("✓ Candidate matching enabled")
    print("✓ Web interface: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)