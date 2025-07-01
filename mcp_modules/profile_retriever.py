"""
Profile Retriever Module
Loads and updates user profile JSON files
"""

import json
import os
from typing import Dict, Any


class ProfileRetriever:
    def __init__(self, profiles_dir: str = "profiles"):
        """Initialize with profiles directory"""
        self.profiles_dir = profiles_dir
        self._ensure_directory_exists()
    
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
                "name": user_id,
                "email": f"{user_id}@example.com",
                "education": [],
                "experience": [],
                "skills": [],
                "resume_path": None,
                "cover_letter_path": None
            }
            self.save_profile(user_id, default_profile)
            return default_profile
        
        try:
            with open(profile_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading profile for {user_id}: {e}")
            return {}
    
    def save_profile(self, user_id: str, profile_data: Dict[str, Any]):
        """
        Save user profile to JSON file
        
        Args:
            user_id (str): User identifier
            profile_data (Dict): Profile data to save
        """
        profile_path = os.path.join(self.profiles_dir, f"{user_id}.json")
        
        try:
            with open(profile_path, 'w') as f:
                json.dump(profile_data, f, indent=2)
        except Exception as e:
            print(f"Error saving profile for {user_id}: {e}")
    
    # def update_profile_paths(self, user_id: str, resume_path: str = None, cover_letter_path: str = None):
    #     """
    #     Update file paths in user profile
        
    #     Args:
    #         user_id (str): User identifier
    #         resume_path (str): Path to generated resume
    #         cover_letter_path (str): Path to generated cover letter
    #     """
    #     profile = self.load_profile(user_id)
        
    #     if resume_path:
    #         profile["resume_path"] = resume_path
    #     if cover_letter_path:
    #         profile["cover_letter_path"] = cover_letter_path
        
    #     self.save_profile(user_id, profile)


def profile_retriever(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    MCP-compliant function to retrieve user profile
    
    Args:
        context: Dict with 'input' containing 'user_id'
        
    Returns:
        Updated context with user profile in 'output'
    """
    retriever = ProfileRetriever()
    user_id = context["input"]["user_id"]
    
    profile = retriever.load_profile(user_id)
    
    if "output" not in context:
        context["output"] = {}
    
    context["output"]["user_profile"] = profile
    context["output"]["retriever"] = retriever  # For later use in updates
    
    return context