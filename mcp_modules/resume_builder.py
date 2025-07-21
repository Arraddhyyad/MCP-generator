"""
Resume Builder Module
Generates tailored resumes from user profile and job information
"""

import os
import pdfkit
from jinja2 import Template
from typing import Dict, Any
import json
from utils import safe_string_processing


class ResumeBuilder:
    def __init__(self, outputs_dir: str = "outputs"):
        """Initialize with outputs directory"""
        self.outputs_dir = outputs_dir
        self.resume_template = self._get_resume_template()
    
    def _ensure_directory_exists(self, path: str):
        """Create directory if it doesn't exist"""
        if not os.path.exists(path):
            os.makedirs(path)
    
    def _get_resume_template(self) -> str:
        """Return HTML template for resume"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Resume - {{ name }}</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
                h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
                h2 { color: #34495e; margin-top: 30px; }
                .contact { margin-bottom: 20px; }
                .section { margin-bottom: 25px; }
                ul { padding-left: 20px; }
                li { margin-bottom: 5px; }
                .highlight { color: #e74c3c; font-weight: bold; }
            </style>
        </head>
        <body>
            <h1>{{ name }}</h1>
            <div class="contact">
                <strong>Email:</strong> {{ email }}<br>
                {% if job_title %}<strong>Position Applied:</strong> <span class="highlight">{{ job_title }}</span>{% endif %}
            </div>
            
            {% if education %}
            <div class="section">
                <h2>Education</h2>
                <ul>
                {% for edu in education %}
                    <li>{{ edu }}</li>
                {% endfor %}
                </ul>
            </div>
            {% endif %}
            
            {% if experience %}
            <div class="section">
                <h2>Experience</h2>
                <ul>
                {% for exp in experience %}
                    <li>{{ exp }}</li>
                {% endfor %}
                </ul>
            </div>
            {% endif %}
            
            {% if skills %}
            <div class="section">
                <h2>Skills</h2>
                <ul>
                {% for skill in skills %}
                    <li>{{ skill }}</li>
                {% endfor %}
                </ul>
            </div>
            {% endif %}
            
            {% if relevant_skills %}
            <div class="section">
                <h2>Relevant Skills for {{ job_title }}</h2>
                <ul>
                {% for skill in relevant_skills %}
                    <li class="highlight">{{ skill }}</li>
                {% endfor %}
                </ul>
            </div>
            {% endif %}
        </body>
        </html>
        """
    
    def generate_resume(self, user_profile: Dict[str, Any], job_info: Dict[str, Any], user_id: str) -> str:
        """
        Generate tailored resume PDF
        
        Args:
            user_profile: User's profile data
            job_info: Job information extracted from email
            user_id: User identifier
            
        Returns:
            Path to generated resume PDF
        """
        # Create user output directory
        user_output_dir = os.path.join(self.outputs_dir, user_id)
        self._ensure_directory_exists(user_output_dir)
        
        # Prepare template data
        template_data = {
            "name": user_profile.get("name", user_id),
            "email": user_profile.get("email", ""),
            "education": safe_string_processing(user_profile.get("education", []), to_lower=False),
            "experience": safe_string_processing(user_profile.get("experience", []), to_lower=False),
            "skills": safe_string_processing(user_profile.get("skills", []), to_lower=False),
            "job_title": job_info.get("job_title", ""),
            "relevant_skills": self._find_relevant_skills(
                user_profile.get("skills", []), 
                job_info.get("skills", [])
            )
        }
        
        # Render HTML
        template = Template(self.resume_template)
        html_content = template.render(**template_data)
        
        # Generate PDF
        resume_path = os.path.join(user_output_dir, "resume.pdf")
        
        try:
            # Configure pdfkit options
            options = {
                'page-size': 'A4',
                'margin-top': '0.75in',
                'margin-right': '0.75in',
                'margin-bottom': '0.75in',
                'margin-left': '0.75in',
                'encoding': "UTF-8",
                'no-outline': None
            }
            
            config = pdfkit.configuration(wkhtmltopdf="/usr/local/bin/wkhtmltopdf")
            pdfkit.from_string(html_content, resume_path, options=options, configuration=config)
            return resume_path
            
        except Exception as e:
            print(f"Error generating PDF: {e}")
            # Fallback: save as HTML
            html_path = os.path.join(user_output_dir, "resume.html")
            with open(html_path, 'w') as f:
                f.write(html_content)
            return html_path
    
    def _find_relevant_skills(self, user_skills: list, job_skills: list) -> list:
        """Find skills that match between user and job requirements"""
        if not job_skills:
            return []
        
        relevant = []
        user_skills_clean = safe_string_processing(user_skills, to_lower=True)
        job_skills_clean = safe_string_processing(job_skills, to_lower=True)
        relevant = [job for job in job_skills if any(job.lower() in user for user in user_skills_clean or user in job.lower() for user in user_skills_clean)]

        return relevant


def resume_builder(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    MCP-compliant function to build resume or reuse if already exists
    """
    builder = ResumeBuilder()
    
    user_profile = context["output"]["user_profile"]
    job_info = context["output"]["job_info"]
    user_id = context["input"]["user_id"]
    
    profile_path = os.path.join("profiles", f"{user_id}.json")
    resume_path = None

    # Check if resume already exists
    if os.path.exists(profile_path):
        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                profile_data = json.load(f)
            
            existing_resume_path = profile_data.get("resume_path")
            if existing_resume_path and os.path.exists(existing_resume_path):
                print(f"✅ Reusing existing resume for {user_id}")
                resume_path = existing_resume_path
        except Exception as e:
            print(f"Error reading profile JSON for {user_id}: {e}")

    # If not cached, generate and update
    if not resume_path:
        resume_path = builder.generate_resume(user_profile, job_info, user_id)
        
        # Update profile JSON with resume_path
        if os.path.exists(profile_path):
            try:
                with open(profile_path, "r", encoding="utf-8") as f:
                    profile_data = json.load(f)
                
                profile_data["resume_path"] = resume_path
                
                with open(profile_path, "w", encoding="utf-8") as f:
                    json.dump(profile_data, f, indent=2)
            except Exception as e:
                print(f"Error updating profile JSON for {user_id}: {e}")
    
    # Final context update
    context["output"]["resume_path"] = resume_path
    
    # Optional: update retriever tool
    if "retriever" in context["output"]:
        context["output"]["retriever"].update_profile_paths(user_id, resume_path=resume_path)
    
    return context