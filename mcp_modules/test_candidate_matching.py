import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mcp_modules.email_interpreter import EmailInterpreter
from mcp_modules.profile_retriever import profile_retriever
import traceback

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_candidate_matching.py '<email_text>'")
        return
    
    email_text = sys.argv[1]
    print(f"Input email text: {email_text}")
    
    try:
        # Step 1: Interpret email
        print("\n=== Step 1: Email Interpretation ===")
        interpreter = EmailInterpreter()
        interpreted = interpreter.interpret_email(email_text)
        print(f"Interpreted job info: {interpreted}")
        
        # Step 2: Build context
        print("\n=== Step 2: Building Context ===")
        context = {
            "input": {"email_text": email_text},
            "output": {"job_info": interpreted},
            "coordination": {
                "request_type": "find_best_candidate",
                "user_id": "FIND_BEST_CANDIDATE",
                "use_candidate_matcher": True
            }
        }
        print(f"Context: {context}")
        
        # Step 3: Run through profile retriever
        print("\n=== Step 3: Profile Retriever Processing ===")
        result = profile_retriever(context)
        print(f"Profile retriever result keys: {list(result.keys())}")
        
        print("\n=== Candidate Matching Result ===")
        if "output" in result:
            output = result["output"]
            print(f"Output keys: {list(output.keys())}")
            
            candidate_result = output.get("candidate_matching_result", {})
            if candidate_result.get("status") == "success":
                best = candidate_result.get("best_candidate")
                if best:
                    print(f"Best candidate: {best.get('name', 'N/A')}")
                    print(f"Email: {best.get('email', 'N/A')}")
                    print(f"Skills: {', '.join(best.get('skills', []))}")
                    print(f"Overall Score: {best.get('overall_score', 'N/A')}")
                    
                    # Show other candidates if available
                    other_candidates = candidate_result.get("other_candidates", [])
                    if other_candidates:
                        print(f"\nOther candidates ({len(other_candidates)}):")
                        for i, candidate in enumerate(other_candidates[:3], 1):  # Show top 3
                            print(f"  {i}. {candidate.get('name', 'N/A')} - Score: {candidate.get('overall_score', 'N/A')}")
                else:
                    print("No candidate found.")
            else:
                error_msg = candidate_result.get('message', 'Unknown error')
                print(f"Error: {error_msg}")
                
                # Additional debugging info
                if "error_details" in candidate_result:
                    print(f"Error details: {candidate_result['error_details']}")
        else:
            print("No output in result")
            print(f"Full result: {result}")
            
    except Exception as e:
        print(f"Exception occurred: {str(e)}")
        print(f"Exception type: {type(e).__name__}")
        print("\nFull traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    main()