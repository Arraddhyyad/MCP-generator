import openai
import json
import os
from typing import Dict, Any
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
            r'screen\s+(?:our\s+)?(?:candidate\s+)?profiles?',
            r'most\s+suitable\s+candidate',
            r'share\s+(?:the\s+)?(?:most\s+)?suitable\s+candidate',
            r'please\s+share\s+(?:the\s+)?(?:candidate|profile)',
            r'send\s+(?:the\s+)?(?:most\s+)?suitable\s+candidate',
            r'share\s+(?:the\s+)?(?:best|right|appropriate)\s+candidate',
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
        Detect if the email is asking for a specific user's resume or to find the best candidate.
        Uses regex first, then falls back to OpenAI for ambiguous cases.
        """
        email_lower = email_text.lower()

        # 1. Regex for "find best candidate"
        for pattern in self.find_candidate_patterns:
            if re.search(pattern, email_lower):
                return "find_best_candidate"

        # 2. Regex for specific user request
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

        # 3. Fallback to OpenAI for classification
        try:
            prompt = f"""
            Does the following email ask to find or recommend the best or most suitable candidate from available profiles? 
            Answer only "yes" or "no".

            Email:
            {email_text}
            """
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert in understanding HR requests."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=3
            )
            answer = response.choices[0].message.content.strip().lower()
            if "yes" in answer:
                return "find_best_candidate"
        except Exception as e:
            print(f"OpenAI fallback failed: {e}")

        return "general_job_posting"
