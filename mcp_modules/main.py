"""
Main Orchestrator for MCP Resume + Cover Letter Generator
Coordinates all modules in the correct sequence
"""

import os
import sys
from typing import Dict, Any

# Add the mcp_modules directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'mcp_modules'))

from email_interpreter import email_interpreter
from profile_retriever import profile_retriever
from resume_builder import resume_builder
from cover_letter_writer import cover_letter_writer
from reply_email_generator import reply_email_generator

class MCPOrchestrator:
    """Main orchestrator for the MCP system"""
    
    def __init__(self):
        """Initialize the orchestrator"""
        self.modules = [
            email_interpreter,
            profile_retriever,
            resume_builder,
            cover_letter_writer,
            reply_email_generator
        ]
    
    def process_email(self, email_text: str, user_id: str) -> Dict[str, Any]:
        """
        Process an HR email through all modules
        
        Args:
            email_text (str): Raw email content
            user_id (str): User identifier
            
        Returns:
            Complete processing context with all outputs
        """
        
        # Initialize context
        context = {
            "input": {
                "email_text": email_text,
                "user_id": user_id
            },
            "output": {}
        }
        
        print(f"Processing email for user: {user_id}")
        
        # Process through all modules sequentially
        for i, module in enumerate(self.modules):
            try:
                print(f"Step {i+1}: Running {module.__name__}...")
                context = module(context)
                print(f"✓ {module.__name__} completed successfully")
            except Exception as e:
                print(f"✗ Error in {module.__name__}: {e}")
                raise
        
        return context
    
    def print_results(self, context: Dict[str, Any]):
        """Print processing results in a formatted way"""
        
        print("PROCESSING COMPLETE")
        
        # Job Information
        job_info = context["output"].get("job_info", {})
        print(f"\n📋 JOB INFORMATION:")
        print(f"   Position: {job_info.get('job_title', 'N/A')}")
        print(f"   Company: {job_info.get('company', 'N/A')}")
        print(f"   Required Skills: {', '.join(job_info.get('skills', []))}")
        print(f"   Action Needed: {job_info.get('action_needed', 'N/A')}")
        
        # Generated Files
        print(f"\n📁 GENERATED FILES:")
        print(f"   Resume: {context['output'].get('resume_path', 'N/A')}")
        print(f"   Cover Letter: {context['output'].get('cover_letter_path', 'N/A')}")
        
        # Email Content
        print(f"\n📧 REPLY EMAIL:")
        print(f"   Subject: {context['output'].get('email_subject', 'N/A')}")
        print(f"\n   Body:\n{context['output'].get('email_body', 'N/A')}")
        
       


def main():
    """Main function to run the MCP system"""
    
    # Check for required environment variables
    if not os.getenv('OPENAI_API_KEY'):
        print("  Warning: OPENAI_API_KEY environment variable not set")
    
    # Example usage
    orchestrator = MCPOrchestrator()
    
    # Test email content
    test_email = """
    Hi Aradhya,
    
    Thank you for your interest in our Machine Learning Intern position at TechCorp.
    We would like to move forward with your application.
    
    Could you please send us your updated resume and a cover letter highlighting your 
    experience with Python, machine learning, and data analysis?
    
    We'd like to review your materials by Friday.
    
    Best regards,
    Sarah Johnson
    HR Manager, TechCorp
    """
    
    test_user_id = "aradhya123"
    
    try:
        # Process the email
        result = orchestrator.process_email(test_email, test_user_id)
        
        # Display results
        orchestrator.print_results(result)
        
        print(f"\n All files have been generated in the 'outputs/{test_user_id}/' directory")
        print(f" User profile updated in 'profiles/{test_user_id}.json'")
        
    except Exception as e:
        print(f"\n Error processing email: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()