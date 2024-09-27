"""
This module provides a manager for interacting with assistants module.
"""

from .assistant import AssistantManager

__all__ = ['AssistantManager']
__version__ = '0.1.0'
__author__ = 'David'

# Assistant manager initialization
manager = AssistantManager()

# Assistant initialization parameters
assistant_name = 'penelope'
model = 'ft:gpt-4o-mini-2024-07-18:novatide-limited:penelope-base-formatted:ABWOPZKM'
system_instructions = """You are Penelope, an exceptionally polite and intelligent AI Assistant. 
You specialize in creating detailed analyses, writing concise summaries, conducting thorough 
information searches, and retrieving real-time data efficiently.
You are a multi-skilled AI assistant, capable of performing a wide range of tasks. 
You can use code interpreter to perform calculations, search the web, and answer questions.
You can also use file search to search for information in a file.
You can use functions to perform specific tasks.
"""

tool_choice = {"type": "function", "function": {"name": "my_function"}}
tool_resources = tool_resources={
    "file_search": {
      "vector_store_ids": ["vs_9m79TZqChZcUjhY1QZPjVnnZ", "vs_itfm8Bn3yn9kI3guPPecbEjh"]
    }
}
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
        {
            "type": "function",
            "function": {
                "name": "get_coin_history",
                "description": "Extract historical data of tokens/coins, volumne, market cap, price...",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "coin_id": {
                            "type": "string",
                            "description": "name of the coin",
                        },
                        "date": {
                            "type": "string",
                            "description": "specific date",
                        },
                    },
                    "required": ["coin_id", "date"],
                    },
            },
        }, 
    ]

# Usage examples

# Create assistant
# assistant = manager.create_assistant(assistant_name, model, system_instructions, tools)
# print('assistant: ', assistant)

# Update assistant
# assistant_id = "asst_VdfcHanMyyhsvEGF48GicLWv"
# response_update = manager.update_assistant(assistant_id=assistant_id,
#                          tool_resources=tool_resources,
#                         # model=model
#                          )
# print('response_update: ', response_update)

# List assistants
# assistants = manager.list_assistants()
# print("List of Assistants:", assistants)

# Delete assistant
# assistant_id = ""
# response_delete = manager.delete_assistant(assistant_id=assistant_id)
# print('response_delete: ', response_delete)

