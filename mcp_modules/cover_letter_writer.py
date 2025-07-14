"""
Cover Letter Writer Module
Generates personalized cover letters using OpenAI
"""

import openai
import os
import pdfkit
from jinja2 import Template
from typing import Dict, Any


class CoverLetterWriter:
    def __init__(self, api_key: str = None, outputs_dir: str = "outputs"):
        """Initialize with OpenAI API key and outputs directory"""
        self.client = openai.OpenAI(
            api_key=api_key or os.getenv('OPENAI_API_KEY')
        )
        self.outputs_dir = outputs_dir
        self.cover_letter_template = self._get_cover_letter_template()
    
    def _ensure_directory_exists(self, path: str):
        """Create directory if it doesn't exist"""
        if not os.path.exists(path):
            os.makedirs(path)
    
    def _get_cover_letter_template(self) -> str:
        """Return HTML template for cover letter"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Cover Letter - {{ name }}</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.8; }
                .header { margin-bottom: 30px; }
                .date { margin-bottom: 20px; }
                .content { margin-bottom: 30px; }
                .signature { margin-top: 40px; }
                p { margin-bottom: 15px; }
                .highlight { color: #2c3e50; font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="header">
                <strong>{{ name }}</strong><br>
                {{ email }}<br>
                {% if phone %}{{ phone }}<br>{% endif %}
            </div>
            
            <div class="date">
                Date: {{ date }}
            </div>
            
            {% if company %}
            <div class="recipient">
                <strong>{{ company }}</strong><br>
                Hiring Team<br>
            </div>
            {% endif %}
            
            <div class="content">
                <p><strong>Subject: Application for <span class="highlight">{{ job_title }}</span></strong></p>
                
                {{ cover_letter_content | safe }}
            </div>
            
            <div class="signature">
                <p>Sincerely,<br>
                <strong>{{ name }}</strong></p>
            </div>
        </body>
        </html>
        """
    
    def generate_cover_letter_content(self, user_profile: Dict[str, Any], job_info: Dict[str, Any]) -> str:
        """
        Generate cover letter content using OpenAI
        
        Args:
            user_profile: User's profile data
            job_info: Job information extracted from email
            
        Returns:
            Generated cover letter content
        """
        
        prompt = f"""
        Write a professional cover letter for the following job application:
        
        Candidate Information:
        - Name: {user_profile.get('name', 'Candidate')}
        - Education: {', '.join(user_profile.get('education', []))}
        - Experience: {', '.join(user_profile.get('experience', []))}
        - Skills: {', '.join(user_profile.get('skills', []))}
        
        Job Information:
        - Position: {job_info.get('job_title', 'Position')}
        - Company: {job_info.get('company', 'Company')}
        - Required Skills: {', '.join(job_info.get('skills', []))}
        
        Requirements:
        1. Write 3-4 paragraphs
        2. Be professional and enthusiastic
        3. Highlight relevant experience and skills
        4. Match the candidate's background to the job requirements
        5. Return HTML formatted paragraphs using <p> tags
        6. Don't include salutation or closing - just the body content
        
        Write the cover letter content:
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert cover letter writer. Write professional, engaging cover letters that highlight the candidate's strengths."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error generating cover letter content: {e}")
            return f"""
            <p>Dear Hiring Manager,</p>
            <p>I am writing to express my strong interest in the {job_info.get('job_title', 'position')} role at {job_info.get('company', 'your company')}.</p>
            <p>With my background in {', '.join(user_profile.get('education', ['relevant field']))}, I believe I would be a valuable addition to your team.</p>
            <p>I look forward to discussing how my skills and experience can contribute to your organization's success.</p>
            """
    
    def generate_cover_letter(self, user_profile: Dict[str, Any], job_info: Dict[str, Any], user_id: str) -> str:
        """
        Generate complete cover letter PDF
        
        Args:
            user_profile: User's profile data
            job_info: Job information extracted from email
            user_id: User identifier
            
        Returns:
            Path to generated cover letter PDF
        """
        # Create user output directory
        user_output_dir = os.path.join(self.outputs_dir, user_id)
        self._ensure_directory_exists(user_output_dir)
        
        # Generate cover letter content
        cover_letter_content = self.generate_cover_letter_content(user_profile, job_info)
        
        # Prepare template data
        from datetime import datetime
        template_data = {
            "name": user_profile.get("name", user_id),
            "email": user_profile.get("email", ""),
            "phone": user_profile.get("phone", ""),
            "company": job_info.get("company", ""),
            "job_title": job_info.get("job_title", "Position"),
            "date": datetime.now().strftime("%B %d, %Y"),
            "cover_letter_content": cover_letter_content
        }
        
        # Render HTML
        template = Template(self.cover_letter_template)
        html_content = template.render(**template_data)
        
        # Generate PDF
        cover_letter_path = os.path.join(user_output_dir, "cover_letter.pdf")
        
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
            pdfkit.from_string(html_content, cover_letter_path, options=options, configuration=config)
            return cover_letter_path
            
        except Exception as e:
            print(f"Error generating cover letter PDF: {e}")
            # Fallback: save as HTML
            html_path = os.path.join(user_output_dir, "cover_letter.html")
            with open(html_path, 'w') as f:
                f.write(html_content)
            return html_path


def cover_letter_writer(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    MCP-compliant function to write cover letter
    
    Args:
        context: Dict with 'output' containing 'user_profile' and 'job_info'
        
    Returns:
        Updated context with cover letter path
    """
    writer = CoverLetterWriter()
    
    user_profile = context["output"]["user_profile"]
    job_info = context["output"]["job_info"]
    user_id = context["input"]["user_id"]
    
    cover_letter_path = writer.generate_cover_letter(user_profile, job_info, user_id)
    
    # Update context
    context["output"]["cover_letter_path"] = cover_letter_path
    
    # Update profile with cover letter path
    if "retriever" in context["output"]:
        context["output"]["retriever"].update_profile_paths(user_id, cover_letter_path=cover_letter_path)
    
    return context