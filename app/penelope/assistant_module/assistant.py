from openai import OpenAI
from typing import List, Dict, Any, Optional
import logging

class AssistantManager:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.logger = logging.getLogger(__name__)

    def create_assistant(self, model: str, name: str, instructions: str, 
                         tools: Optional[List[Dict[str, Any]]] = None, 
                         temperature: float = 0.5) -> Dict[str, Any]:
        """
        Create a new assistant with the specified parameters.
        """
        try:
            assistant = self.client.beta.assistants.create(
                model=model,
                name=name,
                instructions=instructions,
                tools=tools or [],
                temperature=temperature
            )
            return assistant
        except Exception as e:
            self.logger.error(f"Error creating assistant: {str(e)}")
            raise

    def list_assistants(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        List all assistants, up to the specified limit.
        """
        try:
            assistants = self.client.beta.assistants.list(limit=limit)
            return [assistant.model_dump() for assistant in assistants.data]
        except Exception as e:
            self.logger.error(f"Error listing assistants: {str(e)}")
            raise

    def delete_assistant(self, assistant_id: str) -> Dict[str, Any]:
        """
        Delete an assistant by its ID.
        """
        try:
            deleted_assistant = self.client.beta.assistants.delete(assistant_id)
            return deleted_assistant.model_dump()
        except Exception as e:
            self.logger.error(f"Error deleting assistant: {str(e)}")
            raise

    def update_assistant(self, assistant_id: str, **kwargs) -> Dict[str, Any]:
        """
        Update an assistant with the provided parameters.
        """
        try:
            updated_assistant = self.client.beta.assistants.update(assistant_id, **kwargs)
            return updated_assistant.model_dump()
        except Exception as e:
            self.logger.error(f"Error updating assistant: {str(e)}")
            raise



# Example usage
import os

# Retrieve API key from environment variable
api_key = os.getenv("OPENAI_API_KEY")
assistant_id = os.getenv("ASSISTANT_ID")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set")

manager = AssistantManager(api_key)

# Update assistant
assistant_name = 'penelope'
model = 'gpt-4o'
system_instructions = "You are Penelope, an exceptionally polite and intelligent AI Assistant. You specialize in creating detailed analyses, writing concise summaries, conducting thorough information searches, and retrieving real-time data efficiently."
tools=[ {"type": "code_interpreter"}, 
        {"type": "file_search"},
        {
            "type": "function",
            "function": {
                "name": "get_latest_news",
                "description": "Retrieves the latest news related to the specified token from a given API endpoint and returns the content of each article",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "coin": {
                            "type": "string",
                            "description": "name of the token, e.g. solana",
                        },
                    },
                    "required": ["coin"],
                    },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_token_data",
                "description": "Fetch detailed data about a cryptocurrency token from the CoinGecko API",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "coin": {
                            "type": "string",
                            "description": "name of the coin, e.g. solana",
                        },
                    },
                    "required": ["coin"],
                    },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_llama_chains",
                "description": "Fetch total value locked (TVL)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "token_id": {
                            "type": "string",
                            "description": "ID of the token e.g. sol",
                        },
                    },
                    "required": ["token_id"],
                    },
            },
        }, 
        {
            "type": "function",
            "function": {
                "name": "extract_data",
                "description": "goes to the specified url and extract the data for further analyses",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "URL of the site",
                        },
                    },
                    "required": ["url"],
                    },
            },
        }, 
    ]

# response_update = manager.update_assistant(assistant_id=assistant_id,
#                          tools=tools
#                          )
# print('response_update: ', response_update)

# # List assistants
# assistants = manager.list_assistants()
# print("List of Assistants:", assistants)
