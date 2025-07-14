"""
Enhanced Email Interpreter Module
Extracts job information from HR emails using OpenAI with sector detection and latest job requirements
"""
import openai
import json
import os
from typing import Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class EmailInterpreter:
    def __init__(self, api_key: str = None):
        """Initialize with OpenAI API key"""
        self.client = openai.OpenAI(
            api_key=api_key or os.getenv('OPENAI_API_KEY')
        )
        
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
        Enhanced email interpretation with user ID extraction, sector detection and latest requirements
        """
        # First, extract user ID from email text
        user_id_prompt = f"""
        Extract the username/user ID mentioned in this email. Look for patterns like:
        - "resume of [username]"
        - "profile of [username]"
        - "[username] for this job"
        - "send [username]'s resume"
        
        Email content:
        {email_text}
        
        Return only the username/user ID found, or "default_user" if none found.
        """
        
        extracted_user_id = "default_user"
        try:
            user_response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert at extracting usernames from text. Return only the username, nothing else."},
                    {"role": "user", "content": user_id_prompt}
                ],
                temperature=0.1
            )
            
            extracted_user_id = user_response.choices[0].message.content.strip()
            if not extracted_user_id or extracted_user_id == "None":
                extracted_user_id = "default_user"
                
        except Exception as e:
            print(f"Error extracting user ID: {e}")
            extracted_user_id = "default_user"
        
        # Now extract basic job information
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
            
            # Add the extracted user ID to the job info
            basic_info["user_id"] = extracted_user_id
            
            # Detect company sector
            sector = self.detect_company_sector(email_text, basic_info.get("company"))
            
            # Get latest requirements for the sector
            latest_requirements = self.get_latest_requirements(sector)
            
            # If no specific skills mentioned, use sector-specific trending skills
            if not basic_info.get("skills") or len(basic_info.get("skills", [])) == 0:
                basic_info["skills"] = latest_requirements["trending_skills"][:5]  # Top 5 skills
            
            # Add sector-specific information
            basic_info["detected_sector"] = sector
            
            # Add enhanced requirements based on sector
            basic_info["recommended_skills"] = latest_requirements["trending_skills"]
            basic_info["required_soft_skills"] = latest_requirements["soft_skills"]
            basic_info["relevant_certifications"] = latest_requirements["certifications"]
            
            # Add market context
            basic_info["market_trends"] = f"Latest trends for {sector} sector as of {datetime.now().strftime('%Y-%m-%d')}"
            
            return basic_info
            
        except Exception as e:
         print(f"Error in email_interpreter: {e}")
        # Return error context with default job_info
        return {
            "status": "error",
            "error": str(e),
            "output": {
                "job_info": {
                    "job_title": "General Position",
                    "company": "Unknown Company",
                    "skills": ["Communication", "Problem-solving", "Teamwork"],
                    "deadline": None,
                    "action_needed": "send resume",
                    "detected_sector": "other",
                    "recommended_skills": ["Communication", "Problem-solving", "Teamwork"],
                    "required_soft_skills": ["Adaptability", "Time management"],
                    "relevant_certifications": ["Industry-specific certifications"],
                    "market_trends": "General industry trends"
                }
            }
        }