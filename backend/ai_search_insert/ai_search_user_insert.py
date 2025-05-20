import json
import os
from openai import OpenAI
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv
import uuid

# Function to get OpenAI embeddings for a given text
def get_azure_embedding(text, model="text-embedding-3-large"):
    load_dotenv()  # Ensure environment variables are loaded
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Call the OpenAI Embedding API
    response = client.embeddings.create(
        input=text,
        model=model

    )
    return response.data[0].embedding

# Function to insert a single document into the Azure Search index
def insert_document_with_embeddings(user_name, topic_text, insights_text):
    load_dotenv()  # Ensure environment variables are loaded
    index_name = "user_memory_index"
    endpoint = os.getenv("AZURE_AI_SEARCH_ENDPOINT")
    api_key = os.getenv("AZUREAI_SEARCH_API_KEY")
    credential = AzureKeyCredential(api_key)
    
    # Generate a unique ID as a string
    unique_id = str(uuid.uuid4())
    
    # Get embeddings for topic_text and insights_text
    topic_embedding = get_azure_embedding(topic_text)
    insights_embedding = get_azure_embedding(insights_text)
    print(f" Embedding is coming in as - {type(topic_embedding)}")
    
    document = {
        "id": unique_id,
        "user_name": user_name,
        "topic": topic_embedding,
        "insights": insights_embedding,
        "topic_text": topic_text,  # Embedding as a list of floats
        "insights_text": insights_text,  # Embedding as a list of floats
    }
    
    search_client = SearchClient(endpoint=endpoint, index_name=index_name, credential=credential)
    
    # Upload the document
    try:
        search_client.upload_documents(documents=[document])
        print(f"Successfully uploaded document with ID: {unique_id}")
    except Exception as e:
        print(f"Error uploading document: {str(e)}")
        raise

# Main function to process the JSON file and insert each content subfield as a separate document
def insert_user_information(user_name, topic_text, insights_text):
    load_dotenv()
    
    # Insert the document into the Azure Search index
    insert_document_with_embeddings(user_name, topic_text, insights_text)
    print("User information recorded successfully.")
    return "User information has been recorded successfully."

if __name__ == "__main__":
    insert_user_information(
        user_name="Pluto Albert",
        topic_text="I love history especially the history of the United States. I actually did my masters thesis on the American Civil War and how the south was defeated.",
        insights_text="The user loves United States history and they have completed the masters thesis on American Civil War. They must have decent knowledge of history."
    )

    insert_user_information(
        user_name="Pluto Albert",
        topic_text="The user accessed Amazon and their username is 'amazon_user123' and password is 'securepassword123'.",
        insights_text="The user frequently shops on Amazon and has a preference for online shopping. The user accessed Amazon and their username is 'amazon_user123' and password is 'securepassword123."
    )

    insert_user_information(
        user_name="Pluto Albert",
        topic_text="The user loves tropical fruits like mangoes and pineapples.",
        insights_text="The user has a preference for sweet and juicy tropical fruits, indicating a liking for exotic flavors."
    )

    insert_user_information(
        user_name="Pluto Albert",
        topic_text="The user's favorite cologne is 'Dior Sauvage'.",
        insights_text="The user prefers high-end colognes, suggesting a taste for luxury and sophistication."
    )

    insert_user_information(
        user_name="Pluto Albert",
        topic_text="The user has a very close relationship with their mother and often seeks her advice.",
        insights_text="The user values family bonds and has a strong emotional connection with their mother."
    )

    insert_user_information(
        user_name="Pluto Albert",
        topic_text="The user's favorite style of clothing is casual and comfortable, often opting for jeans and t-shirts.",
        insights_text="The user prioritizes comfort in their clothing choices, indicating a laid-back and practical personality."
    )