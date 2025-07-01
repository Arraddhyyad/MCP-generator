"""
Email Interpreter Module
Extracts job information from HR emails using OpenAI
"""

import openai
import json
import os
from typing import Dict, Any


class EmailInterpreter:
    def __init__(self, api_key: str = None):
        """Initialize with OpenAI API key"""
        self.client = openai.OpenAI(
            api_key=api_key or os.getenv('OPENAI_API_KEY')
        )
    
    def interpret_email(self, email_text: str) -> Dict[str, Any]:
        """
        Extract job information from email text using OpenAI
        
        Args:
            email_text (str): Raw email content
            
        Returns:
            Dict containing job_title, company, skills, deadline, action_needed
        """
        
        prompt = f"""
        Analyze this HR email and extract the following information in JSON format:
        - job_title: The position being offered/discussed
        - company: Company name (if mentioned)
        - skills: List of required/preferred skills mentioned
        - deadline: Any deadline mentioned for response
        - action_needed: What action is being requested (apply, send resume, etc.)
        
        Email content:
        {email_text}
        
        Return only valid JSON with these fields. If information is not found, use null.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing job-related emails. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"Error interpreting email: {e}")
            return {
                "job_title": None,
                "company": None,
                "skills": [],
                "deadline": None,
                "action_needed": "send resume"
            }


def email_interpreter(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    MCP-compliant function to interpret email content
    
    Args:
        context: Dict with 'input' containing 'email_text'
        
    Returns:
        Updated context with job information in 'output'
    """
    interpreter = EmailInterpreter()
    email_text = context["input"]["email_text"]
    
    job_info = interpreter.interpret_email(email_text)
    
    # Update context
    if "output" not in context:
        context["output"] = {}
    
    context["output"]["job_info"] = job_info
    
    return context