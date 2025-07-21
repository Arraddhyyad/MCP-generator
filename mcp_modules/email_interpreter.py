"""
Enhanced Email Interpreter Module with Candidate Matching
Extracts job information from HR emails and can find best candidates from profiles
"""
import openai
import json
import os
from typing import Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv
import re
from utils import safe_string_processing

load_dotenv()

class EmailInterpreter:
    def __init__(self, api_key: str = None):
        """Initialize with OpenAI API key"""
        self.client = openai.OpenAI(
            api_key=api_key or os.getenv('OPENAI_API_KEY')
        )
        
        # Patterns to detect "find best candidate" requests
        self.find_candidate_patterns = [
            r'find\s+(?:the\s+)?best\s+candidate',
            r'who\s+(?:is\s+)?(?:the\s+)?best\s+(?:suited\s+)?(?:for\s+)?(?:this\s+)?(?:job|position|role)',
            r'recommend\s+(?:a\s+)?candidate',
            r'suggest\s+(?:a\s+)?(?:suitable\s+)?candidate',
            r'which\s+candidate\s+(?:is\s+)?(?:best\s+)?(?:suited\s+)?(?:for\s+)?(?:this\s+)?(?:job|position|role)',
            r'select\s+(?:the\s+)?(?:best\s+)?candidate',
            r'choose\s+(?:the\s+)?(?:best\s+)?candidate',
            r'match\s+(?:a\s+)?candidate\s+(?:for\s+)?(?:this\s+)?(?:job|position|role)',
            r'pick\s+(?:the\s+)?(?:best\s+)?candidate',
            r'identify\s+(?:the\s+)?(?:best\s+)?candidate',
            r'shortlist\s+(?:the\s+)?(?:best\s+)?candidate',
            r'from\s+(?:our\s+)?(?:available\s+)?(?:candidate\s+)?profiles?',
            r'from\s+(?:our\s+)?(?:talent\s+)?(?:pool|database)',
            r'review\s+(?:our\s+)?(?:candidate\s+)?profiles?',
            r'screen\s+(?:our\s+)?(?:candidate\s+)?profiles?'
        ]
        
        # Latest industry trends and requirements (2024-2025)
        self.sector_requirements = {
            "technology": {
                "trending_skills": ["AI/ML", "Cloud Computing", "Kubernetes", "React", "Python", "DevOps", "Cybersecurity", "Data Science"],
                "soft_skills": ["Remote collaboration", "Agile methodology", "Problem-solving", "Communication"],
                "certifications": ["AWS Certified", "Google Cloud Professional", "Microsoft Azure", "Kubernetes Certified"]
            },
            "finance": {
                "trending_skills": ["Fintech", "Blockchain", "Risk Management", "Data Analytics", "Regulatory Compliance", "API Integration"],
                "soft_skills": ["Attention to detail", "Analytical thinking", "Client communication", "Regulatory knowledge"],
                "certifications": ["CFA", "FRM", "PMP", "Certified Fintech Professional"]
            },
            "healthcare": {
                "trending_skills": ["Telemedicine", "Healthcare IT", "HIPAA Compliance", "EMR Systems", "Medical Coding", "Data Privacy"],
                "soft_skills": ["Patient care", "Empathy", "Detail-oriented", "Team collaboration"],
                "certifications": ["HIPAA Certified", "Medical coding certification", "Healthcare IT certification"]
            },
            "marketing": {
                "trending_skills": ["Digital Marketing", "SEO/SEM", "Social Media", "Content Creation", "Analytics", "CRM", "Marketing Automation"],
                "soft_skills": ["Creativity", "Communication", "Data interpretation", "Brand awareness"],
                "certifications": ["Google Analytics", "HubSpot", "Facebook Blueprint", "Google Ads"]
            },
            "sales": {
                "trending_skills": ["CRM Software", "Sales Analytics", "Lead Generation", "Customer Relationship Management", "Sales Automation"],
                "soft_skills": ["Persuasion", "Relationship building", "Negotiation", "Active listening"],
                "certifications": ["Salesforce Certified", "HubSpot Sales", "Sales methodology certifications"]
            },
            "consulting": {
                "trending_skills": ["Strategic Planning", "Business Analysis", "Project Management", "Data Analysis", "Change Management"],
                "soft_skills": ["Problem-solving", "Communication", "Leadership", "Adaptability"],
                "certifications": ["PMP", "Certified Management Consultant", "Business Analysis certifications"]
            },
            "education": {
                "trending_skills": ["E-learning platforms", "Educational technology", "Curriculum development", "Online teaching", "Assessment tools"],
                "soft_skills": ["Patience", "Communication", "Adaptability", "Empathy"],
                "certifications": ["Teaching certification", "Educational technology certifications"]
            }
        }

    def detect_request_type(self, email_text: str) -> str:
        """
        Detect if the email is asking for a specific user's resume or to find the best candidate
        """
        email_lower = email_text.lower()
        
        # Check for "find best candidate" patterns
        for pattern in self.find_candidate_patterns:
            if re.search(pattern, email_lower):
                return "find_best_candidate"
        
        # Check for specific user request patterns
        user_patterns = [
            r'resume\s+(?:of\s+|for\s+)?([a-zA-Z0-9_]+)',
            r'profile\s+(?:of\s+|for\s+)?([a-zA-Z0-9_]+)',
            r'send\s+([a-zA-Z0-9_]+)(?:\'s)?\s+resume',
            r'([a-zA-Z0-9_]+)\s+(?:for\s+)?(?:this\s+)?(?:job|position|role)',
            r'hire\s+([a-zA-Z0-9_]+)',
            r'consider\s+([a-zA-Z0-9_]+)',
            r'([a-zA-Z0-9_]+)\s+(?:would\s+be\s+)?(?:suitable|good|perfect)\s+(?:for\s+)?(?:this\s+)?(?:job|position|role)'
        ]
        
        for pattern in user_patterns:
            if re.search(pattern, email_lower):
                return "specific_user"
        
        return "general_job_posting"

    def extract_user_id(self, email_text: str) -> str:
        """
        Extract specific user ID from email text
        """
        email_lower = email_text.lower()
        
        # Patterns to find user ID
        user_patterns = [
            r'resume\s+(?:of\s+|for\s+)?([a-zA-Z0-9_]+)',
            r'profile\s+(?:of\s+|for\s+)?([a-zA-Z0-9_]+)',
            r'send\s+([a-zA-Z0-9_]+)(?:\'s)?\s+resume',
            r'([a-zA-Z0-9_]+)\s+(?:for\s+)?(?:this\s+)?(?:job|position|role)',
            r'hire\s+([a-zA-Z0-9_]+)',
            r'consider\s+([a-zA-Z0-9_]+)',
            r'([a-zA-Z0-9_]+)\s+(?:would\s+be\s+)?(?:suitable|good|perfect)\s+(?:for\s+)?(?:this\s+)?(?:job|position|role)'
        ]
        
        for pattern in user_patterns:
            match = re.search(pattern, email_lower)
            if match:
                user_id = match.group(1).strip()
                if user_id and len(user_id) > 1:  # Ensure it's not just a single letter
                    return user_id
        
        return "default_user"

    def detect_company_sector(self, email_text: str, company_name: str = None) -> str:
        """
        Detect company sector from email content and company name
        """
        prompt = f"""
        Analyze this email and determine the company sector/industry. Consider:
        - Company name (if mentioned): {company_name}
        - Email content and context
        - Job role mentioned
        - Industry-specific terminology used
        
        Email content:
        {email_text}
        
        Return only one of these sectors:
        - technology
        - finance
        - healthcare
        - marketing
        - sales
        - consulting
        - education
        - other
        
        If uncertain, choose the most likely sector based on context.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert at identifying company sectors and industries. Return only the sector name."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            sector = response.choices[0].message.content.strip().lower()
            return sector if sector in self.sector_requirements else "other"
            
        except Exception as e:
            print(f"Error detecting sector: {e}")
            return "other"

    def get_latest_requirements(self, sector: str) -> Dict[str, Any]:
        """
        Get latest job requirements for a specific sector
        """
        if sector not in self.sector_requirements:
            return {
                "trending_skills": ["Communication", "Problem-solving", "Teamwork"],
                "soft_skills": ["Adaptability", "Time management", "Critical thinking"],
                "certifications": ["Industry-specific certifications"]
            }
        
        return self.sector_requirements[sector]

    def interpret_email(self, email_text: str) -> Dict[str, Any]:
        """
        Enhanced email interpretation with request type detection
        """
        # Detect the type of request
        request_type = self.detect_request_type(email_text)
        
        # Extract basic job information using OpenAI
        basic_prompt = f"""
        Analyze this HR email and extract the following information in JSON format:
        - job_title: The position being offered/discussed
        - company: Company name (if mentioned)
        - skills: List of required/preferred skills mentioned
        - deadline: Any deadline mentioned for response
        - action_needed: What action is being requested (apply, send resume, etc.)
        - salary_range: Salary or compensation mentioned (if any)
        - location: Work location mentioned (if any)
        - experience_level: Required experience level (entry, mid, senior)
        - employment_type: Full-time, part-time, contract, etc.
        
        Email content:
        {email_text}
        
        Return only valid JSON with these fields. If information is not found, use null.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing job-related emails. Return only valid JSON."},
                    {"role": "user", "content": basic_prompt}
                ],
                temperature=0.3
            )
            
            basic_info = json.loads(response.choices[0].message.content)
            
            # Handle different request types
            if request_type == "find_best_candidate":
                basic_info["user_id"] = "FIND_BEST_CANDIDATE"
                basic_info["request_type"] = "find_best_candidate"
                basic_info["action_needed"] = "find and recommend best candidate from profiles"
                basic_info["use_candidate_matcher"] = True  # NEW: Flag for profile retriever
            elif request_type == "specific_user":
                extracted_user_id = self.extract_user_id(email_text)
                basic_info["user_id"] = extracted_user_id
                basic_info["request_type"] = "specific_user"
                basic_info["action_needed"] = f"send resume and cover letter for {extracted_user_id}"
                basic_info["use_candidate_matcher"] = False
            else:
                basic_info["user_id"] = "default_user"
                basic_info["request_type"] = "general_job_posting"
                basic_info["action_needed"] = "send resume and cover letter"
                basic_info["use_candidate_matcher"] = False
            
            # Detect company sector
            sector = self.detect_company_sector(email_text, basic_info.get("company"))
            
            # Get latest requirements for the sector
            latest_requirements = self.get_latest_requirements(sector)
            
            # If no specific skills mentioned, use sector-specific trending skills
            if not basic_info.get("skills") or len(basic_info.get("skills", [])) == 0:
                basic_info["skills"] = latest_requirements["trending_skills"][:5]  # Top 5 skills
            
            # Add sector-specific information
            basic_info["detected_sector"] = sector
            basic_info["recommended_skills"] = latest_requirements["trending_skills"]
            basic_info["required_soft_skills"] = latest_requirements["soft_skills"]
            basic_info["relevant_certifications"] = latest_requirements["certifications"]
            
            # Add market context
            basic_info["market_trends"] = f"Latest trends for {sector} sector as of {datetime.now().strftime('%Y-%m-%d')}"
            
            # Store original email for candidate matcher
            basic_info["original_email"] = email_text
            
            return basic_info
            
        except Exception as e:
            print(f"Error in email_interpreter: {e}")
            # Return error context with default job_info
            return {
                "job_title": "General Position",
                "company": "Unknown Company",
                "skills": ["Communication", "Problem-solving", "Teamwork"],
                "deadline": None,
                "action_needed": "send resume",
                "user_id": "default_user",
                "request_type": "general_job_posting",
                "detected_sector": "other",
                "recommended_skills": ["Communication", "Problem-solving", "Teamwork"],
                "required_soft_skills": ["Adaptability", "Time management"],
                "relevant_certifications": ["Industry-specific certifications"],
                "market_trends": "General industry trends",
                "use_candidate_matcher": False,
                "original_email": email_text,
                "error": str(e)
            }


# MCP-compliant function for email interpretation
def email_interpreter(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    MCP-compliant function to interpret email and set up context for profile retrieval
    
    Args:
        context: Dict with 'input' containing 'email_text'
    
    Returns:
        Updated context with job_info and coordination flags
    """
    try:
        interpreter = EmailInterpreter()
        email_text = context.get("input", {}).get("email_text", "")
        
        job_info = interpreter.interpret_email(email_text)
        
        if "output" not in context:
            context["output"] = {}
        
        context["output"]["job_info"] = job_info
        context["status"] = "success"
        
        # Set coordination flags for profile retriever
        context["coordination"] = {
            "request_type": job_info.get("request_type", "general_job_posting"),
            "user_id": job_info.get("user_id", "default_user"),
            "use_candidate_matcher": job_info.get("use_candidate_matcher", False),
            "original_email": job_info.get("original_email", email_text)
        }
        
        return context
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "output": {},
            "coordination": {
                "request_type": "general_job_posting",
                "user_id": "default_user",
                "use_candidate_matcher": False,
                "original_email": context.get("input", {}).get("email_text", "")
            }
        }