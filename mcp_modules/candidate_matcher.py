"""
Candidate Matcher Module
Finds the best candidate from profiles based on job requirements
"""
import json
import os
from typing import Dict, Any, List, Union
from sentence_transformers import SentenceTransformer, util
import torch
from mcp_modules.email_interpreter import EmailInterpreter
from mcp_modules.profile_retriever import ProfileRetriever
from utils import safe_string_processing

class CandidateMatcher:
    def __init__(self):
        """Initialize with email interpreter, profile retriever, and embedding model"""
        self.email_interpreter = EmailInterpreter()
        self.profile_retriever = ProfileRetriever()
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            print(f"Warning: Could not load embedding model: {e}")
            self.embedding_model = None

    def safe_string_processing(self, items: Union[List[str], List[Any], str, None]) -> List[str]:
        """Safely process various input types to a list of lowercase strings"""
        if not items:
            return []

        if isinstance(items, str):
            return [item.strip().lower() for item in items.split(',') if item and item.strip()]

        if isinstance(items, list):
            processed = []
            for item in items:
                if item is not None:
                    if isinstance(item, str):
                        processed.append(item.strip().lower())
                    elif isinstance(item, dict):
                        # Prefer 'name' if available
                        if 'name' in item:
                            processed.append(str(item['name']).strip().lower())
                        else:
                            processed.append(json.dumps(item).lower())
                    else:
                        processed.append(str(item).lower())
            return [item for item in processed if item]

        return []


    def calculate_skills_match(self, job_skills: List[str], candidate_skills: List[str]) -> float:
        """Calculate skills match with improved error handling"""
        try:
            # Safely process both skill lists
            job_skills_clean = self.safe_string_processing(job_skills)
            candidate_skills_clean = self.safe_string_processing(candidate_skills)
            
            print(f"Debug - Job skills processed: {job_skills_clean}")
            print(f"Debug - Candidate skills processed: {candidate_skills_clean}")
            
            if not job_skills_clean or not candidate_skills_clean:
                return 0.0

            # Use embedding model if available, otherwise fall back to keyword matching
            if self.embedding_model:
                try:
                    job_embeddings = self.embedding_model.encode(job_skills_clean, convert_to_tensor=True)
                    candidate_embeddings = self.embedding_model.encode(candidate_skills_clean, convert_to_tensor=True)
                    similarity_matrix = util.cos_sim(job_embeddings, candidate_embeddings)
                    best_matches = torch.max(similarity_matrix, dim=1).values
                    score = round(torch.mean(best_matches).item(), 2)
                    print(f"Debug - Embedding-based skills match: {score}")
                    return score
                except Exception as e:
                    print(f"Warning: Embedding calculation failed: {e}, falling back to keyword matching")
            
            # Fallback to keyword matching
            matches = 0
            for job_skill in job_skills_clean:
                for candidate_skill in candidate_skills_clean:
                    if job_skill in candidate_skill or candidate_skill in job_skill:
                        matches += 1
                        break
            
            score = round(matches / len(job_skills_clean), 2) if job_skills_clean else 0.0
            print(f"Debug - Keyword-based skills match: {score} ({matches}/{len(job_skills_clean)})")
            return score
            
        except Exception as e:
            print(f"Error in skills matching: {str(e)}")
            return 0.0

    def calculate_experience_match(self, job_level: str, candidate_experience: Union[List[Dict], List[str], str]) -> float:
        """Calculate experience match with improved handling"""
        try:
            if not candidate_experience:
                return 0.1 if job_level and job_level.lower() == "entry" else 0.0
            
            # Handle different experience formats
            if isinstance(candidate_experience, str):
                # Simple string experience
                years_indicators = ['year', 'yr', 'experience', 'exp']
                exp_lower = candidate_experience.lower()
                if any(indicator in exp_lower for indicator in years_indicators):
                    total_years = 2  # Default assumption for string experience
                else:
                    total_years = 1
            elif isinstance(candidate_experience, list):
                if not candidate_experience:
                    return 0.1
                # Count experiences or extract years
                total_years = len(candidate_experience)
                
                # Try to extract actual years from experience descriptions
                year_count = 0
                for exp in candidate_experience:
                    if isinstance(exp, dict):
                        exp_str = json.dumps(exp).lower()
                    else:
                        exp_str = str(exp).lower()
                    
                    # Look for year indicators
                    import re
                    year_matches = re.findall(r'(\d+)\s*(?:year|yr)', exp_str)
                    if year_matches:
                        year_count += sum(int(match) for match in year_matches)
                
                if year_count > 0:
                    total_years = year_count
            else:
                total_years = 1
            
            # Match against level requirements
            level_requirements = {
                "entry": (0, 2),
                "junior": (0, 2),
                "mid": (2, 5),
                "intermediate": (2, 5),
                "senior": (5, 10),
                "expert": (10, 20),
                "lead": (5, 15)
            }
            
            if job_level:
                job_level_clean = job_level.lower().strip()
                if job_level_clean in level_requirements:
                    min_years, max_years = level_requirements[job_level_clean]
                    if min_years <= total_years <= max_years:
                        return 1.0
                    elif total_years > max_years:
                        return 0.8  # Overqualified but still good
                    else:
                        return max(0.2, (total_years / max(min_years, 1)) * 0.6)
            
            # Default scoring based on experience amount
            if total_years >= 5:
                return 0.9
            elif total_years >= 2:
                return 0.7
            elif total_years >= 1:
                return 0.5
            else:
                return 0.3
                
        except Exception as e:
            print(f"Error in experience matching: {str(e)}")
            return 0.5

    def calculate_education_match(self, job_requirements: Dict, candidate_education: Union[List[Dict], List[str], str]) -> float:
        """Calculate education match with improved handling"""
        try:
            if not candidate_education:
                return 0.3  # Base score for no education info
            
            education_score = 0.5  # Base score for having education
            
            # Extract relevance keywords safely
            relevance_keywords = []
            if job_requirements:
                job_title = job_requirements.get('job_title', '')
                if job_title:
                    relevance_keywords.append(job_title.lower())
                
                company = job_requirements.get('company', '')
                if company:
                    relevance_keywords.append(company.lower())
                
                skills = job_requirements.get('skills', [])
                if skills:
                    skill_keywords = self.safe_string_processing(skills)
                    relevance_keywords.extend(skill_keywords)
            
            # Process education data
            education_text = ""
            if isinstance(candidate_education, str):
                education_text = candidate_education.lower()
            elif isinstance(candidate_education, list):
                education_parts = []
                for edu in candidate_education:
                    if isinstance(edu, dict):
                        education_parts.append(json.dumps(edu).lower())
                    else:
                        education_parts.append(str(edu).lower())
                education_text = " ".join(education_parts)
            
            # Check for keyword matches
            matches = 0
            for keyword in relevance_keywords:
                if keyword and keyword in education_text:
                    matches += 1
            
            if matches > 0:
                education_score = min(0.5 + (matches * 0.1), 1.0)
            
            # Bonus for higher education keywords
            higher_ed_keywords = ['bachelor', 'master', 'phd', 'doctorate', 'engineering', 'computer science', 'technology']
            for keyword in higher_ed_keywords:
                if keyword in education_text:
                    education_score = min(education_score + 0.1, 1.0)
                    break
            
            return round(education_score, 2)
            
        except Exception as e:
            print(f"Error in education matching: {str(e)}")
            return 0.3

    def calculate_overall_match(self, skills_score: float, experience_score: float, education_score: float) -> float:
        """Calculate weighted overall match score"""
        return round(skills_score * 0.6 + experience_score * 0.3 + education_score * 0.1, 2)

    def find_best_candidate(self, email_text: str = None,
                          job_requirements: Dict[str, Any] = None,
                          profiles: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Find the best candidate with improved error handling"""
        try:
            print(f"=== Candidate Matcher Debug ===")
            
            # Get job requirements
            if not job_requirements and email_text:
                print("Interpreting email for job requirements...")
                job_requirements = self.email_interpreter.interpret_email(email_text)
                print(f"Job requirements: {job_requirements}")
            
            if not job_requirements:
                return {"status": "error", "message": "No job requirements provided"}
            
            # Get profiles
            if not profiles:
                print("Loading profiles from directory...")
                profiles_dir = self.profile_retriever.profiles_dir
                if not os.path.exists(profiles_dir):
                    return {"status": "error", "message": "No profiles directory found"}
                
                profile_files = [f for f in os.listdir(profiles_dir) if f.endswith('.json')]
                print(f"Found {len(profile_files)} profile files")
                
                profiles = []
                for filename in profile_files:
                    try:
                        profile = self.profile_retriever.load_profile(filename.replace('.json', ''))
                        if profile:
                            profiles.append(profile)
                    except Exception as e:
                        print(f"Error loading profile {filename}: {e}")
                        continue
            
            if not profiles:
                return {"status": "error", "message": "No valid profiles found"}
            
            print(f"Processing {len(profiles)} profiles...")
            candidates = []
            
            for i, profile in enumerate(profiles):
                try:
                    print(f"\n--- Processing candidate {i+1}: {profile.get('name', 'Unknown')} ---")
                    
                    # Calculate scores with error handling
                    skills_score = self.calculate_skills_match(
                        job_requirements.get('skills', []) or job_requirements.get('required_skills', []),
                        profile.get('skills', [])
                    )
                    
                    experience_score = self.calculate_experience_match(
                        job_requirements.get('experience_level', 'entry'),
                        profile.get('experience', [])
                    )
                    
                    education_score = self.calculate_education_match(
                        job_requirements, 
                        profile.get('education', [])
                    )
                    
                    overall_score = self.calculate_overall_match(skills_score, experience_score, education_score)
                    
                    print(f"Scores - Skills: {skills_score}, Experience: {experience_score}, Education: {education_score}, Overall: {overall_score}")
                    
                    candidates.append({
                        "user_id": profile.get('user_id', f'candidate_{i+1}'),
                        "name": profile.get('name', profile.get('user_id', f'Candidate {i+1}')),
                        "email": profile.get('email', f"{profile.get('user_id', f'candidate{i+1}')}@example.com"),
                        "phone": profile.get('phone', 'Not provided'),
                        "skills": safe_string_processing(profile.get('skills', []), to_lower=False),
                        "experience": profile.get('experience', []),
                        "education": profile.get('education', []),
                        "breakdown": {
                            "skills_match": f"{skills_score:.2f}",
                            "experience_match": f"{experience_score:.2f}",
                            "education_match": f"{education_score:.2f}",
                            "overall_match": f"{overall_score:.2f}"
                        },
                        "overall_score": overall_score
                    })
                    
                except Exception as e:
                    print(f"Error processing candidate {i+1}: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            if not candidates:
                return {"status": "error", "message": "No valid candidate profiles could be processed"}
            
            # Sort by overall score
            candidates.sort(key=lambda x: x['overall_score'], reverse=True)
            
            print(f"\n=== Final Results ===")
            print(f"Best candidate: {candidates[0]['name']} (Score: {candidates[0]['overall_score']})")
            
            return {
                "status": "success",
                "best_candidate": candidates[0],
                "all_candidates": candidates[:5],  # Top 5 candidates
                "job_requirements": job_requirements,
                "total_candidates_evaluated": len(candidates)
            }
            
        except Exception as e:
            print(f"Critical error in candidate matching: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "message": f"Error in candidate matching: {str(e)}"}

# MCP-compliant function
def candidate_matcher(context: Dict[str, Any]) -> Dict[str, Any]:
    """MCP-compliant wrapper function"""
    try:
        print("=== MCP Candidate Matcher Called ===")
        print(f"Context keys: {list(context.keys())}")
        
        matcher = CandidateMatcher()
        
        # Extract parameters from context
        job_requirements = None
        email_text = None
        profiles = None
        
        if "output" in context:
            job_requirements = context["output"].get("job_info")
            print(f"Job requirements from context: {job_requirements}")
        
        if "input" in context:
            email_text = context["input"].get("email_text")
            profiles = context["input"].get("all_profiles")
            print(f"Email text: {email_text}")
            print(f"Profiles provided: {len(profiles) if profiles else 0}")
        
        # Find best candidate
        result = matcher.find_best_candidate(
            email_text=email_text,
            job_requirements=job_requirements,
            profiles=profiles
        )
        
        # Update context
        if "output" not in context:
            context["output"] = {}
        context["output"]["candidate_matching_result"] = result
        
        print(f"Matching result status: {result.get('status')}")
        return context
        
    except Exception as e:
        print(f"Error in MCP candidate_matcher: {str(e)}")
        import traceback
        traceback.print_exc()
        
        if "output" not in context:
            context["output"] = {}
        context["output"]["candidate_matching_result"] = {
            "status": "error",
            "message": f"Error in candidate matching: {str(e)}"
        }
        return context