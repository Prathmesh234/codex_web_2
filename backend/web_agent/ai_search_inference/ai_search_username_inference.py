##This is for implementing purely a text based search in order to get the user information, if the user is not found we will return user not found
from azure.search.documents import SearchClient
from dotenv import load_dotenv
import os
from azure.core.credentials import AzureKeyCredential
from pydantic import BaseModel, Field
from typing import List, Optional
from pydantic import BaseModel, Field
from typing import Optional

class UserInformation(BaseModel):
    id: str = Field(..., description="Unique identifier for the user")
    user_name: str = Field(..., description="Name of the user")
    topic_text: Optional[str] = Field(None, description="Topic text related to the user")
    insights_text: Optional[str] = Field(None, description="Insights text related to the user")

load_dotenv()
# Create the SearchClient to interact with the index
endpoint = os.getenv("AZURE_AI_SEARCH_ENDPOINT")
index_name = "user_memory_index"
api_key = os.getenv("AZUREAI_SEARCH_API_KEY")
credential = AzureKeyCredential(api_key)
search_client = SearchClient(endpoint=endpoint, index_name=index_name, credential=credential)

# Function to perform vector search (synchronous version)
def search_index(user_name, k: int = 10):
    # Perform the search
    results = search_client.search(
        search_text=user_name,  # Input query for semantic search
        top=k,  # Number of top results to return
        query_type="simple",  # Use semantic search
        search_fields=["user_name"]  # Enable highlighting in captions
    )
    
    # Return the results
    return results

def search_user_name(user_name: str) -> dict:
    """
    Search for a user and return all their information or a not found message

    Args:
        user_name (str): Name of the user to search for

    Returns:
        dict: Result containing either all user data or not found message
    """
    if not user_name or not user_name.strip():
        return {
            "status": "not_found",
            "message": "Invalid user name: Name cannot be empty"
        }

    try:
        results = search_index(user_name, k=5)
        results_list = list(results)

        if not results_list:
            return {
                "status": "not_found",
                "message": f"User '{user_name}' not found in the database"
            }

        # Validate and extract all information about the user
        user_data = []
        validation_errors = []

        for result in results_list:
            try:
                validated_data = UserInformation(
                    id=result["id"],
                    user_name=result["user_name"],
                    topic_text=result.get("topic_text"),
                    insights_text=result.get("insights_text")
                )
                # Verify the user_name matches exactly
                if validated_data.user_name.lower() == user_name.lower():
                    user_data.append(validated_data.dict())
            except Exception as e:
                validation_errors.append(str(e))
                print(f"Validation error: {e}")

        if not user_data:
            # If we had results but none matched exactly
            return {
                "status": "not_found",
                "message": f"No exact match found for user '{user_name}'"
            }

        return {
            "status": "found",
            "data": user_data
        }

    except Exception as e:
        print(f"Error in search_user_name: {str(e)}")
        return {
            "status": "error",
            "message": f"Error searching for user: {str(e)}"
        }

# Example usage
if __name__ == "__main__":
    result = search_user_name("Amazon User")
    if result["status"] == "not_found":
        print(result["message"])
    else:
        print(f"User found: {result['data']}")