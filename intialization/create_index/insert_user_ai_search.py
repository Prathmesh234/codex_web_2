from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchFieldDataType,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    SemanticConfiguration,
    SemanticPrioritizedFields,
    SemanticField,
    ScalarQuantizationCompression,
    SemanticSearch,
    SearchField
)
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv
import os

# Define function to create a scalar-quantized index without truncation
def create_index(index_name, dimensions):
    # Define fields for the index
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True, filterable=True),
        SearchableField(name="user_name", type=SearchFieldDataType.String, filterable=True, searchable=True),
        SearchField(
            name="topic",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            vector_search_dimensions=dimensions,
            vector_search_profile_name="myHnswProfile"
        ),
        SearchField(
            name="insights",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            vector_search_dimensions=dimensions,
            vector_search_profile_name="myHnswProfile"
        ),
        # Add text fields for semantic search
        SearchableField(name="topic_text", type=SearchFieldDataType.String, searchable=True),
        SearchableField(name="insights_text", type=SearchFieldDataType.String, searchable=True)
    ]

    # Define scalar quantization compression configuration without truncation
    compression_name = "myCompression"
    compression_configurations = [
        ScalarQuantizationCompression(compression_name=compression_name)
    ]

    # Define vector search with compression
    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(name="myHnsw")
        ],
        profiles=[
            VectorSearchProfile(
                name="myHnswProfile",
                algorithm_configuration_name="myHnsw",
                compression_name=compression_name
            )
        ],
        compressions=compression_configurations
    )

    # Define semantic configuration with corrected field names
    semantic_config = SemanticConfiguration(
        name="my-semantic-config",
        prioritized_fields=SemanticPrioritizedFields(
            title_field=SemanticField(field_name="insights_text"),  # Corrected to match defined field
            content_fields=[
                SemanticField(field_name="topic_text"),
                SemanticField(field_name="insights_text")
            ]
        )
    )
    semantic_search = SemanticSearch(configurations=[semantic_config])

    return SearchIndex(
        name=index_name,
        fields=fields,
        vector_search=vector_search,
        semantic_search=semantic_search
    )

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    endpoint = os.getenv("AZURE_AI_SEARCH_ENDPOINT")
    api_key = os.getenv("AZUREAI_SEARCH_API_KEY")

    # Validate environment variables
    if not endpoint or not api_key:
        raise ValueError("AZURE_AI_SEARCH_ENDPOINT and AZUREAI_SEARCH_API_KEY must be set in the .env file")

    credential = AzureKeyCredential(api_key)
    index_name = "user_memory_index"
    embedding_dimensions = 3072  # Example dimension size for embeddings

    # Initialize the SearchIndexClient
    search_index_client = SearchIndexClient(endpoint=endpoint, credential=credential)

    # Delete existing index if it exists
    try:
        search_index_client.delete_index(index_name)
        print(f"Deleted existing index: {index_name}")
    except Exception as ex:
        print(f"Index {index_name} did not exist or could not be deleted: {ex}")

    # Create the scalar-quantized index without truncation
    try:
        index = create_index(index_name, dimensions=embedding_dimensions)
        search_index_client.create_or_update_index(index)
        print("Created scalar-quantized index for the semantic_memory_application")
    except Exception as ex:
        print(f"Failed to create index: {ex}")