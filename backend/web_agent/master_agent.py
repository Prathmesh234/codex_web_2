from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.kernel import Kernel
import os
from typing import Optional
import asyncio
from dotenv import load_dotenv

# Assuming these are defined in your codebase
from .system_prompt import MASTER_AGENT_SYSTEM_PROMPT
from .kernel_plugin import MemoryPlugin

async def master_agent(task: str, user_name: Optional[str] = None):
    kernel = Kernel()
    load_dotenv(".env")
    thread = ChatHistoryAgentThread()
    master_agent_name = "master_agent"
    credentials = os.getenv("OPENAI_API_KEY")
    master_service_id = "master_agent"

    # Add the OpenAIChatCompletion service to the kernel
    service = OpenAIChatCompletion(service_id=master_service_id, api_key=credentials, ai_model_id="gpt-4o")
    kernel.add_service(service)

    # Add the memory plugin
    memory_plugin = MemoryPlugin()
    kernel.add_plugin(memory_plugin, plugin_name="memory_plugin")

    # Handle optional user_name
    if user_name:
        user_input = f"The User name is {user_name} and the task is {task}"
    else:
        user_input = f"The task is {task} (no specific user name provided)"

    # Create the master agent with the service instance
    master_agent = ChatCompletionAgent(
        service=service,
        kernel=kernel,
        name=master_agent_name,
        instructions=MASTER_AGENT_SYSTEM_PROMPT
    )

    master_agent_reply = await invoke_agent(master_agent, user_input, thread)
    
    # Since we're now handling user not found cases in the system prompt,
    # we'll always return the master agent's reply
    print(f"Master Agent: {master_agent_reply}")
    return master_agent_reply

async def invoke_agent(agent: ChatCompletionAgent, input: str, thread: ChatHistoryAgentThread) -> Optional[str]:
    """
    Invoke the agent with the user input and return the agent's response.
    
    Args:
        agent: The chat completion agent.
        input: The user's input message.
        thread: The chat history thread to maintain conversation context.
    
    Returns:
        Optional[str]: The agent's response, or None if no valid response is received.
    
    Raises:
        Exception: If the agent invocation fails (e.g., API error).
    """
    if not input.strip():
        return None

    print(f"User: {input}")

    response = ""
    try:
        async for content in agent.invoke(messages=input, thread=thread):
            if content.content is not None:
                print(f"Agent: {content.content}")
                response += str(content.content) + " "
    except Exception as e:
        print(f"Error invoking agent: {e}")
        raise

    return response.strip() if response else None