"""
Enhanced Profile Retriever Module with Email Interpreter Coordination
Loads and updates user profile JSON files with enhanced candidate matching support
Works with email_interpreter to handle different request types:
1. Specific user resume requests
2. Find best candidate requests (calls candidate_matcher)
3. General job postings
"""

import json
import os
from typing import Dict, Any, List, Optional, Tuple
from utils import safe_string_processing


class ProfileRetriever:
    def __init__(self, profiles_dir: str = "profiles"):
        """Initialize with profiles directory"""
        self.profiles_dir = profiles_dir
        self._ensure_directory_exists()
        
        # Special user IDs that trigger different behaviors
        self.FIND_BEST_CANDIDATE_ID = "FIND_BEST_CANDIDATE"
        self.DEFAULT_USER_ID = "default_user"

    def _ensure_directory_exists(self):
        """Create profiles directory if it doesn't exist"""
        if not os.path.exists(self.profiles_dir):
            os.makedirs(self.profiles_dir)

    def load_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Load user profile from JSON file

        Args:
            user_id (str): User identifier

        Returns:
            Dict containing user profile data
        """
        profile_path = os.path.join(self.profiles_dir, f"{user_id}.json")

        if not os.path.exists(profile_path):
            # Create default profile if doesn't exist
            default_profile = {
                "user_id": user_id,
                "name": user_id.replace("_", " ").title(),
                "email": f"{user_id}@example.com",
                "phone": "Not provided",
                "education": [],
                "experience": [],
                "skills": [],
                "resume_path": None,
                "cover_letter_path": None,
                "created_at": None,
                "updated_at": None
            }
            self.save_profile(user_id, default_profile)
            return default_profile

        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile = json.load(f)
                # Ensure user_id is set
                if 'user_id' not in profile:
                    profile['user_id'] = user_id
                return profile
        except Exception as e:
            print(f"Error loading profile for {user_id}: {e}")
            return self._get_default_profile(user_id)

    def _get_default_profile(self, user_id: str) -> Dict[str, Any]:
        """Get default profile structure"""
        return {
            "user_id": user_id,
            "name": user_id.replace("_", " ").title(),
            "email": f"{user_id}@example.com",
            "phone": "Not provided",
            "education": [],
            "experience": [],
            "skills": [],
            "resume_path": None,
            "cover_letter_path": None,
            "created_at": None,
            "updated_at": None
        }

    def save_profile(self, user_id: str, profile_data: Dict[str, Any]):
        """
        Save user profile to JSON file

        Args:
            user_id (str): User identifier
            profile_data (Dict): Profile data to save
        """
        profile_path = os.path.join(self.profiles_dir, f"{user_id}.json")

        try:
            # Ensure user_id is set
            profile_data['user_id'] = user_id
            
            # Add timestamp
            import datetime
            profile_data['updated_at'] = datetime.datetime.now().isoformat()
            if 'created_at' not in profile_data or not profile_data['created_at']:
                profile_data['created_at'] = profile_data['updated_at']

            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving profile for {user_id}: {e}")

    def get_all_profiles(self) -> List[Dict[str, Any]]:
        """
        Get all user profiles for candidate matching

        Returns:
            List of all user profiles
        """
        profiles = []
        
        if not os.path.exists(self.profiles_dir):
            return profiles

        try:
            for filename in os.listdir(self.profiles_dir):
                if not filename.endswith('.json'):
                    continue
                
                user_id = filename.replace('.json', '')
                # Skip the special FIND_BEST_CANDIDATE profile if it exists
                if user_id == self.FIND_BEST_CANDIDATE_ID:
                    continue
                    
                try:
                    profile = self.load_profile(user_id)
                    if profile:
                        profiles.append(profile)
                except Exception as e:
                    print(f"Error loading profile {user_id}: {e}")
                    continue
        except Exception as e:
            print(f"Error accessing profiles directory: {e}")
            
        return profiles

    def handle_coordination_logic(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        NEW: Handle coordination with email interpreter based on request type
        
        Args:
            context: Context from email interpreter with coordination flags
            
        Returns:
            Updated context with appropriate profile data or candidate matching results
        """
        coordination = context.get("coordination", {})
        request_type = coordination.get("request_type", "general_job_posting")
        user_id = coordination.get("user_id", self.DEFAULT_USER_ID)
        use_candidate_matcher = coordination.get("use_candidate_matcher", False)
        
        print(f"ProfileRetriever: Handling request_type='{request_type}', user_id='{user_id}', use_matcher={use_candidate_matcher}")
        
        if request_type == "find_best_candidate" or user_id == self.FIND_BEST_CANDIDATE_ID or use_candidate_matcher:
            # Call candidate matcher instead of loading single profile
            return self._handle_best_candidate_request(context)
        
        elif request_type == "specific_user":
            # Load specific user's profile
            return self._handle_specific_user_request(context, user_id)
        
        else:
            # Default behavior for general job postings
            return self._handle_general_request(context, user_id)

    def _handle_best_candidate_request(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle find best candidate request by calling candidate matcher"""
        try:
            # Import candidate_matcher module
            from . import candidate_matcher
            
            print("ProfileRetriever: Calling candidate_matcher for best candidate selection")
            
            # Get all profiles for candidate matching
            all_profiles = self.get_all_profiles()
            
            if not all_profiles:
                return {
                    "status": "error",
                    "error": "No candidate profiles found",
                    "output": {},
                    "coordination": context.get("coordination", {})
                }
            
            # Add all profiles to context for candidate matcher
            context["input"] = context.get("input", {})
            context["input"]["all_profiles"] = all_profiles
            
            # Call candidate matcher
            result_context = candidate_matcher.candidate_matcher(context)
            
            if result_context.get("status") == "success":
                best_candidate = result_context.get("output", {}).get("best_candidate")
                if best_candidate:
                    # Load the full profile of the best candidate
                    best_user_id = best_candidate.get("user_id")
                    if best_user_id:
                        full_profile = self.load_profile(best_user_id)
                        result_context["output"]["user_profile"] = full_profile
                        result_context["output"]["selected_user_id"] = best_user_id
                        result_context["output"]["selection_method"] = "candidate_matcher"
                        print(f"ProfileRetriever: Selected best candidate: {best_user_id}")
            
            return result_context
            
        except ImportError as e:
            print(f"ProfileRetriever: candidate_matcher module not found: {e}")
            # Fallback to legacy matching
            return self._fallback_candidate_matching(context)
        except Exception as e:
            print(f"ProfileRetriever: Error in candidate matching: {e}")
            return self._fallback_candidate_matching(context)

    def _fallback_candidate_matching(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback candidate matching using legacy method"""
        try:
            job_info = context.get("output", {}).get("job_info", {})
            required_skills = job_info.get("skills", []) or job_info.get("recommended_skills", [])
            
            best_user_id = self.find_best_candidate(required_skills)
            best_profile = self.load_profile(best_user_id)
            
            if "output" not in context:
                context["output"] = {}
                
            context["output"]["user_profile"] = best_profile
            context["output"]["selected_user_id"] = best_user_id
            context["output"]["selection_method"] = "legacy_matching"
            context["output"]["match_reason"] = f"Best skill match for: {', '.join(required_skills[:3])}"
            context["status"] = "success"
            
            print(f"ProfileRetriever: Fallback matching selected: {best_user_id}")
            return context
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Fallback matching failed: {str(e)}",
                "output": {},
                "coordination": context.get("coordination", {})
            }

    def _handle_specific_user_request(self, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Handle specific user profile request"""
        try:
            profile = self.load_profile(user_id)
            
            if "output" not in context:
                context["output"] = {}
                
            context["output"]["user_profile"] = profile
            context["output"]["selected_user_id"] = user_id
            context["output"]["selection_method"] = "specific_user_request"
            context["status"] = "success"
            
            print(f"ProfileRetriever: Loaded specific user profile: {user_id}")
            return context
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to load specific user {user_id}: {str(e)}",
                "output": {},
                "coordination": context.get("coordination", {})
            }

    def _handle_general_request(self, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Handle general job posting request"""
        try:
            # Use default user or provided user_id
            actual_user_id = user_id if user_id != self.FIND_BEST_CANDIDATE_ID else self.DEFAULT_USER_ID
            profile = self.load_profile(actual_user_id)
            
            if "output" not in context:
                context["output"] = {}
                
            context["output"]["user_profile"] = profile
            context["output"]["selected_user_id"] = actual_user_id
            context["output"]["selection_method"] = "default_user"
            context["status"] = "success"
            
            print(f"ProfileRetriever: Loaded default profile: {actual_user_id}")
            return context
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to load default profile: {str(e)}",
                "output": {},
                "coordination": context.get("coordination", {})
            }

    def update_profile_paths(self, user_id: str, resume_path: str = None, cover_letter_path: str = None):
        """
        Update file paths in user profile

        Args:
            user_id (str): User identifier
            resume_path (str): Path to generated resume
            cover_letter_path (str): Path to generated cover letter
        """
        profile = self.load_profile(user_id)

        if resume_path:
            profile["resume_path"] = resume_path
        if cover_letter_path:
            profile["cover_letter_path"] = cover_letter_path

        self.save_profile(user_id, profile)

    def update_profile_field(self, user_id: str, field: str, value: Any):
        """
        Update a specific field in user profile

        Args:
            user_id (str): User identifier
            field (str): Field name to update
            value (Any): New value for the field
        """
        profile = self.load_profile(user_id)
        profile[field] = value
        self.save_profile(user_id, profile)

    def add_skill(self, user_id: str, skill: str):
        """
        Add a skill to user profile

        Args:
            user_id (str): User identifier
            skill (str): Skill to add
        """
        profile = self.load_profile(user_id)
        if 'skills' not in profile:
            profile['skills'] = []
        
        # Avoid duplicates
        if skill not in profile['skills']:
            profile['skills'].append(skill)
            self.save_profile(user_id, profile)

    def add_experience(self, user_id: str, experience: Dict[str, Any]):
        """
        Add experience to user profile

        Args:
            user_id (str): User identifier
            experience (Dict): Experience data
        """
        profile = self.load_profile(user_id)
        if 'experience' not in profile:
            profile['experience'] = []
        
        profile['experience'].append(experience)
        self.save_profile(user_id, profile)

    def add_education(self, user_id: str, education: Dict[str, Any]):
        """
        Add education to user profile

        Args:
            user_id (str): User identifier
            education (Dict): Education data
        """
        profile = self.load_profile(user_id)
        if 'education' not in profile:
            profile['education'] = []
        
        profile['education'].append(education)
        self.save_profile(user_id, profile)

    def find_best_candidate(self, job_skills: List[str]) -> str:
        """
        Find the best matching user profile based on job skills
        (Legacy method - use CandidateMatcher for advanced matching)

        Args:
            job_skills (List[str]): Skills required for the job

        Returns:
            str: User ID of the best matching candidate
        """
        best_score = -1
        best_user = None
        required_skills = set([skill.lower().strip() for skill in job_skills if skill])

        try:
            for filename in os.listdir(self.profiles_dir):
                if not filename.endswith(".json"):
                    continue
                
                user_id = filename.replace(".json", "")
                # Skip special IDs
                if user_id == self.FIND_BEST_CANDIDATE_ID:
                    continue
                    
                try:
                    profile = self.load_profile(user_id)
                    user_skills = set([s.lower().strip() for s in profile.get("skills", []) if s])
                    match_score = len(user_skills & required_skills)
                    
                    if match_score > best_score:
                        best_score = match_score
                        best_user = user_id
                except Exception as e:
                    print(f"Error reading profile {filename}: {e}")
                    continue
        except Exception as e:
            print(f"Error in find_best_candidate: {e}")

        return best_user or self.DEFAULT_USER_ID

    def get_profile_stats(self) -> Dict[str, Any]:
        """
        Get statistics about all profiles

        Returns:
            Dict containing profile statistics
        """
        profiles = self.get_all_profiles()
        
        if not profiles:
            return {
                "total_profiles": 0,
                "profiles_with_skills": 0,
                "profiles_with_experience": 0,
                "profiles_with_education": 0,
                "top_skills": [],
                "avg_skills_per_profile": 0
            }
        
        total_profiles = len(profiles)
        profiles_with_skills = sum(1 for p in profiles if p.get('skills'))
        profiles_with_experience = sum(1 for p in profiles if p.get('experience'))
        profiles_with_education = sum(1 for p in profiles if p.get('education'))
        
        # Count skills
        all_skills = []
        for profile in profiles:
            all_skills.extend(profile.get('skills', []))
        
        skill_counts = {}
        for skill in all_skills:
            skill_lower = skill.lower().strip()
            skill_counts[skill_lower] = skill_counts.get(skill_lower, 0) + 1
        
        top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "total_profiles": total_profiles,
            "profiles_with_skills": profiles_with_skills,
            "profiles_with_experience": profiles_with_experience,
            "profiles_with_education": profiles_with_education,
            "top_skills": top_skills,
            "avg_skills_per_profile": len(all_skills) / total_profiles if total_profiles > 0 else 0
        }

    def search_profiles(self, query: str) -> List[Dict[str, Any]]:
        """
        Search profiles by name, email, or skills

        Args:
            query (str): Search query

        Returns:
            List of matching profiles
        """
        query_lower = query.lower().strip()
        matching_profiles = []
        
        for profile in self.get_all_profiles():
            # Search in name
            if query_lower in profile.get('name', '').lower():
                matching_profiles.append(profile)
                continue
            
            # Search in email
            if query_lower in profile.get('email', '').lower():
                matching_profiles.append(profile)
                continue
            
            # Search in skills
            skills_match = any(query_lower in skill.lower() for skill in profile.get('skills', []))
            if skills_match:
                matching_profiles.append(profile)
                continue
        
        return matching_profiles

    def validate_profile(self, profile: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate profile data

        Args:
            profile (Dict): Profile data to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Required fields
        required_fields = ['user_id', 'name', 'email']
        for field in required_fields:
            if field not in profile or not profile[field]:
                errors.append(f"Missing required field: {field}")
        
        # Email validation (basic)
        if 'email' in profile and profile['email']:
            if '@' not in profile['email']:
                errors.append("Invalid email format")
        
        # Skills validation
        if 'skills' in profile and profile['skills']:
            if not isinstance(profile['skills'], list):
                errors.append("Skills must be a list")
            else:
                for skill in profile['skills']:
                    if not isinstance(skill, str):
                        errors.append("All skills must be strings")
        
        # Experience validation
        if 'experience' in profile and profile['experience']:
            if not isinstance(profile['experience'], list):
                errors.append("Experience must be a list")
        
        # Education validation
        if 'education' in profile and profile['education']:
            if not isinstance(profile['education'], list):
                errors.append("Education must be a list")
        
        return len(errors) == 0, errors


def profile_retriever(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    ENHANCED: MCP-compliant function to retrieve user profile with coordination support
    Now handles coordination with email interpreter for different request types

    Args:
        context: Dict with coordination info from email interpreter

    Returns:
        Updated context with user profile in 'output'
    """
    try:
        retriever = ProfileRetriever()
        
        # Check if we have coordination info from email interpreter
        if "coordination" in context:
            print("ProfileRetriever: Found coordination info from email_interpreter")
            return retriever.handle_coordination_logic(context)
        
        # Fallback to legacy behavior for backward compatibility
        user_id = context.get("input", {}).get("user_id", "default_user")
        profile = retriever.load_profile(user_id)

        if "output" not in context:
            context["output"] = {}

        context["output"]["user_profile"] = profile
        context["output"]["selected_user_id"] = user_id
        context["output"]["selection_method"] = "legacy_direct_call"
        context["output"]["retriever"] = retriever  # For later use in updates
        context["status"] = "success"

        return context
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "output": {},
            "coordination": context.get("coordination", {})
        }


def get_all_profiles(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    MCP-compliant function to get all profiles for candidate matching

    Args:
        context: Dict (user_id not required for this function)

    Returns:
        Updated context with all profiles in 'output'
    """
    try:
        retriever = ProfileRetriever()
        profiles = retriever.get_all_profiles()

        if "output" not in context:
            context["output"] = {}

        context["output"]["all_profiles"] = profiles
        context["output"]["profile_count"] = len(profiles)
        context["status"] = "success"

        return context
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "output": {}
        }