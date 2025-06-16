from .ai_search_inference.ai_search_username_inference import search_user_name
from .ai_search_inference.ai_search_user_inference import search_index
from .ai_search_insert.ai_search_user_insert import insert_user_information
from dotenv import load_dotenv
import os

async def get_user_name(user_name : str):
    username_search_result = search_user_name(user_name)
    if username_search_result["status"] == "not_found":
        print("User not found in the database. Creating a new user")
        return {
            "status" :"not_found", 
            "message": f"User '{user_name}' not found in the database"
        }
    else:
        print(username_search_result["data"])
        return {
            "status": "found",
            "data": username_search_result["data"]
        }

def extract_top_choice(search_results):
    # Sort results by @search.score or @search.reranker_score in descending order
    sorted_results = sorted(search_results, key=lambda x: x.get('@search.score', 0), reverse=True)
    
    # Pick the top result
    if sorted_results:
        top_result = sorted_results[0]
        
        # Extract variables from the top result
        user_id = top_result.get('id', None)
        insights_text = top_result.get('insights_text', None)
        topic_text = top_result.get('topic_text', None)
        user_name = top_result.get('user_name', None)
        
        return {
            "user_id": user_id,
            "insights_text": insights_text,
            "topic_text": topic_text,
            "user_name": user_name
        }
    else:
        return None

async def get_user_information(user_name: str, question: str, k: int = 4):
    print(f"Attempting to get information for user: {user_name}")
    
    if not user_name or not user_name.strip():
        print("Invalid user name: Name cannot be empty")
        return {
            "status": "not_found",
            "message": "Invalid user name: Name cannot be empty"
        }

    user_found_result = await get_user_name(user_name)
    
    if user_found_result["status"] == "not_found":
        print(f"User '{user_name}' not found in the database.")
        return {
            "status": "not_found",
            "message": f"User '{user_name}' not found in the database"
        }
    
    if not user_found_result.get("data"):
        print(f"User '{user_name}' found but has no associated data")
        return {
            "status": "not_found",
            "message": f"User '{user_name}' has no associated data"
        }
    
    print(f"User '{user_name}' found in database with data: {user_found_result['data']}")
    try:
        user_search_result = search_index(question, k)
        
        # First return the user's general information even if specific query yields no results
        base_data = {
            "status": "found",
            "data": {
                "user_info": user_found_result["data"],
                "query_results": None
            }
        }
        
        if not user_search_result:
            base_data["data"]["query_results"] = {"message": "No specific information found for the given query"}
            return base_data
        
        extracted_data = extract_top_choice(user_search_result)
        if not extracted_data:
            base_data["data"]["query_results"] = {"message": "No relevant information found for the given query"}
            return base_data
            
        base_data["data"]["query_results"] = extracted_data
        return base_data
        
    except Exception as e:
        print(f"Error during search: {str(e)}")
        return {
            "status": "error",
            "message": f"Error retrieving user information: {str(e)}"
        }




