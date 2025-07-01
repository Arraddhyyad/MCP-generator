"""
Resume Builder Module
Generates tailored resumes from user profile and job information
"""

import os
import pdfkit
from jinja2 import Template
from typing import Dict, Any


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
            "education": user_profile.get("education", []),
            "experience": user_profile.get("experience", []),
            "skills": user_profile.get("skills", []),
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
            
            pdfkit.from_string(html_content, resume_path, options=options)
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
        for job_skill in job_skills:
            for user_skill in user_skills:
                if job_skill.lower() in user_skill.lower() or user_skill.lower() in job_skill.lower():
                    if job_skill not in relevant:
                        relevant.append(job_skill)
        
        return relevant


def resume_builder(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    MCP-compliant function to build resume
    
    Args:
        context: Dict with 'output' containing 'user_profile' and 'job_info'
        
    Returns:
        Updated context with resume path
    """
    builder = ResumeBuilder()
    
    user_profile = context["output"]["user_profile"]
    job_info = context["output"]["job_info"]
    user_id = context["input"]["user_id"]
    
    resume_path = builder.generate_resume(user_profile, job_info, user_id)
    
    
    context["output"]["resume_path"] = resume_path
    
   
    if "retriever" in context["output"]:
        context["output"]["retriever"].update_profile_paths(user_id, resume_path=resume_path)
    
    return context