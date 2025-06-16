from semantic_kernel.functions.kernel_function_decorator import kernel_function
from typing import Annotated
from .agentic_memory import get_user_information
from .ai_search_insert.ai_search_user_insert import insert_user_information
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel
from .system_prompt import MEMORY_AGENT_SYSTEM_PROMPT
import os
non_persistent_list = [] 
class Memory(BaseModel):
    topic_text : str
    insights_text: str # Define this globally or in a proper memory module

class MemoryPlugin:

    @kernel_function(description="'Retrieve user-specific information (e.g., email, login credentials, resource group names) from the agent's memory. Returns the stored data if it exists, or 'USER NOT FOUND' if it does not.")
    async def retrieve_user_context(self, user_name: Annotated[str, "Name of the user"], agent_query: Annotated[str, "What information do you want from the memory"]) -> Annotated[str, "Returns memory specific to the agent's request"]:
        print(f"Debug: retrieve_user_context called with user_name={user_name}, agent_query={agent_query}")
        
        if not user_name or not user_name.strip():
            print("Debug: Empty or invalid user name provided")
            return "USER NOT FOUND"

        try:
            user_info = await get_user_information(user_name, agent_query, k=2)
            
            if user_info["status"] == "not_found":
                print(f"Debug: User not found - {user_info['message']}")
                return "USER NOT FOUND"
            elif user_info["status"] == "error":
                print(f"Debug: Error retrieving user info - {user_info['message']}")
                return "USER NOT FOUND"
            elif user_info["status"] == "found":
                if not user_info.get("data"):
                    print("Debug: No data found for user")
                    return "USER NOT FOUND"
                    
                user_data = user_info["data"]
                base_info = user_data.get("user_info", [])
                query_results = user_data.get("query_results", {})
                
                # Always return user information if the user exists
                if base_info:
                    response_parts = []
                    for info in base_info:
                        if info.get("topic_text"):
                            response_parts.append(info["topic_text"])
                            
                    if query_results and query_results.get("topic_text"):
                        response_parts.append(f"Specific to your query: {query_results['topic_text']}")
                        
                    return " | ".join(response_parts)
                    
                return str(query_results.get("message", "No specific information found"))
            else:
                print(f"Debug: Unknown status received: {user_info['status']}")
                return "USER NOT FOUND"
                
        except Exception as e:
            print(f"Debug: Exception in retrieve_user_context - {str(e)}")
            return "USER NOT FOUND"
            
    @kernel_function(description='Prompt the user to provide specific information (e.g., email, password, preferences) when it is not found in memory. Pass a clear question as input, and return the user’s response. After every execution of this function, you MUST call store_user_context to persist the information you receive from the user.')
    def prompt_user_for_input(self, question: Annotated[str, "What information you want from the user if you do not get it from the retrieve_user_context "], user_name: Annotated[str, "Name of the user"] = None) -> str:
        print(f"Debug: prompt_user_for_input called with question={question}")
        user_input = input(f"{question}\n")
        # After getting user input, store it using store_user_context
        if user_name:
            self.store_user_context(question, user_input, user_name)
        else:
            print("Warning: user_name not provided to prompt_user_for_input; skipping store_user_context call.")
        return user_input

    @kernel_function(description='Store user-provided information (e.g., email, login, preferences) in the agent’s memory. Provide the question asked and the user’s answer as key-value pairs.')
    def store_user_context(self, question: str, answer: str, user_name: str = None) -> str:
        load_dotenv(".env")
        api_key = os.getenv("OPENAI_API_KEY")
        client = OpenAI(api_key=api_key)
        completion = client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": MEMORY_AGENT_SYSTEM_PROMPT},
            {"role": "user", "content": f"User Question : {question} \n User Answer : {answer}"},
        ],
        response_format=Memory,
        )
        memory = completion.choices[0].message.parsed
        print(f"Debug: store_user_context called with question={question}, answer={answer}, user_name={user_name}")
        non_persistent_list.append({question: answer})
        print(f"Debug: Current memory state: {non_persistent_list}")
        # Persist to Azure Search using insert_user_information
        if user_name:
            try:
                insert_user_information(user_name, memory.topic_text, memory.insights_text)
                print(f"Debug: Persisted user info for {user_name} to Azure Search.")
            except Exception as e:
                print(f"Error persisting user info: {e}")
        else:
            print("Warning: user_name not provided to store_user_context; skipping persistent storage.")
        return "Memory stored successfully!"
