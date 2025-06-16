##Implementation of Hybrid search in azure ai search index 
##This is the inference file stating that the index has been created and the documents are inserted into the index
# And now we just have to run the inference on that search. 
from azure.search.documents import SearchClient
from dotenv import load_dotenv
import os
from azure.core.credentials import AzureKeyCredential
from pydantic import BaseModel, Field
from typing import Optional

class UserInformation(BaseModel):
    id: str = Field(..., description="Unique identifier for the user")
    user_name: str = Field(..., description="Name of the user")
    topic_text: Optional[str] = Field(None, description="Topic text related to the user")
    insights_text: Optional[str] = Field(None, description="Insights text related to the user")

load_dotenv()
# Create the SearchClient to interact with the index
question_new = "Can you get a fruit I would like from Amazon"
endpoint = os.getenv("AZURE_AI_SEARCH_ENDPOINT")
index_name = "user_memory_index"
api_key = os.getenv("AZUREAI_SEARCH_API_KEY")
credential = AzureKeyCredential(api_key)
search_client = SearchClient(endpoint=endpoint, index_name=index_name, credential=credential)

# Function to perform vector search (synchronous version)
def search_index(question, k: int = 2):
    # Perform the search
    results = search_client.search(
        search_text=question,  # Input query for semantic search
        top=k,  # Number of top results to return
        query_type="semantic",  # Use semantic search
        semantic_configuration_name="my-semantic-config",  # Replace with your semantic configuration name
        query_caption="extractive",  # Extractive captions for concise explanations
        query_caption_highlight_enabled=True,  # Enable highlighting in captions
    )

    # Validate and extract all information about the results
    validated_results = []
    for result in results:
        try:
            validated_data = UserInformation(
                id=result["id"],
                user_name=result["user_name"],
                topic_text=result.get("topic_text"),
                insights_text=result.get("insights_text")
            )
            validated_results.append(validated_data.dict())
        except Exception as e:
            print(f"Validation error: {e}")

    return validated_results

# Main function (synchronous)
def main():
    results = search_index(question_new, k=2)
    for result in results:
        print(question_new)
        print(result)

if __name__ == "__main__":
    main()