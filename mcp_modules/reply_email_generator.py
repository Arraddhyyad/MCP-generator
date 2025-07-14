"""
Reply Email Generator Module
Composes professional reply emails with attachments
"""

import openai
import os
from typing import Dict, Any


class ReplyEmailGenerator:
    def __init__(self, api_key: str = None):
        """Initialize with OpenAI API key"""
        self.client = openai.OpenAI(
            api_key=api_key or os.getenv('OPENAI_API_KEY')
        )
    
    def generate_reply_email(self, user_profile: Dict[str, Any], job_info: Dict[str, Any], 
                           resume_path: str, cover_letter_path: str) -> str:
        """
        Generate professional reply email content
        
        Args:
            user_profile: User's profile data
            job_info: Job information extracted from email
            resume_path: Path to generated resume
            cover_letter_path: Path to generated cover letter
            
        Returns:
            Generated email body content
        """
        
        prompt = f"""
        Compose a professional reply email for a job application with the following details:
        
        Candidate: {user_profile.get('name', 'Candidate')}
        Position: {job_info.get('job_title', 'Position')}
        Company: {job_info.get('company', 'Company')}
        Action Requested: {job_info.get('action_needed', 'send resume')}
        
        Requirements:
        1. Professional and concise tone
        2. Express enthusiasm for the position
        3. Mention that resume and cover letter are attached
        4. Thank them for the opportunity
        5. Keep it brief (2-3 short paragraphs)
        6. Don't include subject line or signature
        7. Use proper email formatting
        8. Talk like you're a database and not the person who's information 
        you're sending across. like if they ask you to send across the profile
        data for xyz user, be like: dear <sender name>, please find the 
        files attached.
        
        Write the email body:
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert at writing professional business emails. Keep responses concise and professional."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=400
            )
            
            email_content = response.choices[0].message.content
            
            # Adding  attachment information
            attachments_info = f"""

Attachments:
• Resume: {os.path.basename(resume_path)}
• Cover Letter: {os.path.basename(cover_letter_path)}

Best regards,
{user_profile.get('name', 'Candidate')}
{user_profile.get('email', '')}"""
            
            return email_content + attachments_info
            
        except Exception as e:
            print(f"Error generating reply email: {e}")
            
            # Fallback email template
            return f"""Dear Hiring Team,

Thank you for your interest in my candidacy for the {job_info.get('job_title', 'position')} role at {job_info.get('company', 'your company')}.

I am excited about this opportunity and have attached my resume and cover letter for your review. I believe my background and skills make me a strong fit for this position.

I look forward to hearing from you and discussing how I can contribute to your team.

Attachments:
• Resume: {os.path.basename(resume_path)}
• Cover Letter: {os.path.basename(cover_letter_path)}

Best regards,
{user_profile.get('name', 'Candidate')}
{user_profile.get('email', '')}"""
    
    def get_email_subject(self, job_info: Dict[str, Any], user_profile: Dict[str, Any]) -> str:
        """
        Generate appropriate email subject line
        
        Args:
            job_info: Job information extracted from email
            user_profile: User's profile data
            
        Returns:
            Generated subject line
        """
        job_title = job_info.get('job_title', 'Position')
        name = user_profile.get('name', 'Candidate')
        
        return f"Application for {job_title} - {name}"


def reply_email_generator(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    MCP-compliant function to generate reply email
    
    Args:
        context: Dict with all previous outputs
        
    Returns:
        Updated context with email content
    """
    generator = ReplyEmailGenerator()
    
    user_profile = context["output"]["user_profile"]
    job_info = context["output"]["job_info"]
    resume_path = context["output"]["resume_path"]
    cover_letter_path = context["output"]["cover_letter_path"]
    
    # Generate email content
    email_body = generator.generate_reply_email(
        user_profile, job_info, resume_path, cover_letter_path
    )
    
    email_subject = generator.get_email_subject(job_info, user_profile)
    
    # Update context
    context["output"]["email_body"] = email_body
    context["output"]["email_subject"] = email_subject
    
    return context