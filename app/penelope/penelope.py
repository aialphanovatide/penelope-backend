# import os
# import json
# import time
# from openai import OpenAI
# from typing import List, Any, Dict
# from app.services.scrapper.scrapper import Scraper
# from app.services.coingecko.coingecko import CoinGeckoAPI
# from app.services.news_bot.news_bot import CoinNewsFetcher
# from app.penelope.vector_store_module.vector_store import VectorStoreManager
# from app.services.defillama.defillama import LlamaChainFetcher
# from app.penelope.assistant_module.assistant import AssistantManager

# COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")

# COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
# COINGECKO_HEADERS = {
#     "accept": "application/json",
#     "x-cg-pro-api-key": COINGECKO_API_KEY,
# }

# class OpenAIAssistantManager:
#     def __init__(self, api_key, COINGECKO_HEADERS, COINGECKO_BASE_URL):
#         print("Initializing OpenAIAssistantManager...")
#         self.client = OpenAI(api_key=api_key)
#         self.thread = None
#         self.vector_store = VectorStoreManager(api_key=api_key)
#         self.scraper = Scraper()
#         self.news_fetcher = CoinNewsFetcher()
#         self.defillama = LlamaChainFetcher(coingecko_base_url=COINGECKO_BASE_URL,
#                                             coingecko_headers=COINGECKO_HEADERS
#                                             )
#         self.coins_fetcher = CoinGeckoAPI(coingecko_headers=COINGECKO_HEADERS,
#                                     coingecko_base_url=COINGECKO_BASE_URL
#                                     )
#         print("OpenAIAssistantManager initialized successfully.")

#     def retrieve_assistant(self, assistant_id):
#         print(f"Retrieving assistant with ID: {assistant_id}")
#         assistant = self.client.beta.assistants.retrieve(assistant_id=assistant_id)
#         print(f"Assistant retrieved: {assistant.name}")
#         return assistant

#     def ensure_thread(self):
#         if not self.thread:
#             print("Creating new thread...")
#             self.thread = self.client.beta.threads.create()
#             print(f"New thread created with ID: {self.thread.id}")
#         else:
#             print(f"Using existing thread with ID: {self.thread.id}")
#         return self.thread

#     def add_message(self, content, role="user"):
#         print(f"Adding message to thread. Role: {role}, Content: {content[:50]}...")
#         thread = self.ensure_thread()
#         message = self.client.beta.threads.messages.create(
#             thread_id=thread.id,
#             role=role,
#             content=content
#         )
#         print(f"Message added successfully. Message ID: {message.id}")
#         return message

#     def run_assistant(self, assistant_id):
#         print(f"Running assistant with ID: {assistant_id}")
#         thread = self.ensure_thread()
#         run = self.client.beta.threads.runs.create(
#             thread_id=thread.id,
#             assistant_id=assistant_id
#         )
#         print(f"Assistant run created. Run ID: {run.id}")
#         return run

#     def get_run_status(self, run_id):
#         thread = self.ensure_thread()
#         run = self.client.beta.threads.runs.retrieve(
#             thread_id=thread.id,
#             run_id=run_id
#         )
#         print(f"Run status for Run ID {run_id}: {run.status}")
#         return run.status

#     def get_messages(self):
#         print("Retrieving messages from thread...")
#         thread = self.ensure_thread()
#         messages = self.client.beta.threads.messages.list(thread_id=thread.id)
#         print(f"Retrieved {len(messages.data)} messages.")
#         return messages

#     def wait_for_completion(self, run_id, timeout=300):
#         print(f"Waiting for run completion. Run ID: {run_id}, Timeout: {timeout}s")
#         start_time = time.time()
#         while True:
#             status = self.get_run_status(run_id)
#             elapsed_time = time.time() - start_time
            
#             if status == "completed":
#                 print(f"Run completed successfully. Total time: {elapsed_time:.2f}s")
#                 return True
#             elif status == "requires_action":
#                 print(f"Run requires action. Elapsed time: {elapsed_time:.2f}s")
#                 return "requires_action"
#             elif status in ["failed", "cancelled", "expired"]:
#                 print(f"Run ended with status: {status}. Total time: {elapsed_time:.2f}s")
#                 return False
#             elif status == "cancelling":
#                 print(f"Run is being cancelled. Elapsed time: {elapsed_time:.2f}s")
#             elif status == "in_progress":
#                 print(f"Run is in progress. Elapsed time: {elapsed_time:.2f}s")
#             elif status == "queued":
#                 print(f"Run is queued. Elapsed time: {elapsed_time:.2f}s")
#             elif status == "incomplete":
#                 print(f"Run ended incomplete. Total time: {elapsed_time:.2f}s")
#                 return False
#             else:
#                 print(f"Unknown status: {status}. Elapsed time: {elapsed_time:.2f}s")
            
#             if elapsed_time > timeout:
#                 print(f"Run timed out after {timeout}s")
#                 raise TimeoutError("Run did not complete within the specified timeout.")
            
#             time.sleep(1)

#     def get_assistant_response(self):
#         print("Retrieving assistant's response...")
#         messages = self.get_messages()
#         for message in messages.data:
#             if message.role == "assistant":
#                 response = message.content[0].text.value
#                 print(f"Assistant response found: {response[:50]}...")
#                 return response
#         print("No assistant response found.")
#         return None

#     def _process_tool_calls(self, tool_calls: List[Any]) -> List[Dict[str, str]]:
#         print(f"Processing {len(tool_calls)} tool calls...")
#         tool_outputs = []
#         for tool in tool_calls:
#             print(f"Processing tool: {tool.function.name}")
#             if tool.function.name in ["get_token_data", "get_latest_news", "extract_data", "get_llama_chains"]:
#                 args = json.loads(tool.function.arguments)
                
#                 arg_value = args.get('coin')
#                 url = args.get('url')
#                 token_id = args.get('token_id')

#                 print(f'Tool: {tool.function.name}, Argument: {arg_value or url or token_id}')

#                 output = None
#                 if tool.function.name == 'get_token_data':
#                     output = self.coins_fetcher.get_token_data(arg_value)
#                 elif tool.function.name == 'get_latest_news':
#                     output = self.news_fetcher.get_latest_news(arg_value)
#                 elif tool.function.name == 'extract_data':
#                     output = self.scraper.extract_data(url)
#                 elif tool.function.name == 'get_llama_chains':
#                     output = self.defillama.get_llama_chains(token_id)

#                 tool_outputs.append({
#                     "tool_call_id": tool.id,
#                     "output": str(output)
#                 })
#                 print(f"Tool output generated. Length: {len(str(output))}")
#             else:
#                 print(f"Unknown tool: {tool.function.name}")
        
#         print(f"Processed {len(tool_outputs)} tool outputs.")
#         return tool_outputs

#     def interact_with_assistant(self, assistant_id, user_message):
#         print(f"Starting interaction with assistant. User message: {user_message[:50]}...")
#         self.add_message(user_message)
#         run = self.run_assistant(assistant_id)
        
#         completion_status = self.wait_for_completion(run.id)
        
#         if completion_status == True:
#             print("Run completed. Retrieving final assistant response.")
#             return self.get_assistant_response()
#         elif completion_status == "requires_action":
#             print("Run requires action. Processing tool calls...")
#             run = self.client.beta.threads.runs.retrieve(thread_id=self.thread.id, run_id=run.id)
#             if hasattr(run, 'required_action') and hasattr(run.required_action, 'submit_tool_outputs'):
#                 tool_outputs = self._process_tool_calls(run.required_action.submit_tool_outputs.tool_calls)
#                 if tool_outputs:
#                     print("Submitting tool outputs...")
#                     second_run = self.client.beta.threads.runs.submit_tool_outputs(
#                         thread_id=self.thread.id,
#                         run_id=run.id,
#                         tool_outputs=tool_outputs
#                     )
#                     if self.wait_for_completion(second_run.id):
#                         print("Second run completed. Retrieving final response.")
#                         return self.get_assistant_response()
#                     else:
#                         print(f"Second run failed or was cancelled.")
#                 else:
#                     print("No tool outputs to submit.")
#             else:
#                 print("No tool calls required or `submit_tool_outputs` not found.")
#         else:
#             print("Run failed, was cancelled, or ended incomplete.")
        
#         return "Failed to get a response from the assistant."

#     def reset_thread(self):
#         print("Resetting thread...")
#         self.thread = None
#         print("Thread reset complete.")

# # Initialize the assistant manager
# api_key = os.getenv("OPENAI_API_KEY")
# penelope_manager = OpenAIAssistantManager(api_key, COINGECKO_HEADERS, COINGECKO_BASE_URL)







# ___________________ DB INTEGRATION _____________________________

import os
import json
import time
from openai import OpenAI
from typing import List, Any, Dict
from datetime import datetime
from sqlalchemy.orm import Session
from app.services.scrapper.scrapper import Scraper
from app.services.coingecko.coingecko import CoinGeckoAPI
from app.services.news_bot.news_bot import CoinNewsFetcher
from app.penelope.vector_store_module.vector_store import VectorStoreManager
from app.services.defillama.defillama import LlamaChainFetcher
from app.penelope.assistant_module.assistant import AssistantManager
from config import Message, Thread, Session


class OpenAIAssistantManager:
    def __init__(self, api_key, COINGECKO_HEADERS, COINGECKO_BASE_URL):
        print("Initializing OpenAIAssistantManager...")
        self.client = OpenAI(api_key=api_key)
        self.thread = None
        self.vector_store = VectorStoreManager(api_key=api_key)
        self.scraper = Scraper()
        self.assistant_manager = AssistantManager(api_key=api_key)
        self.news_fetcher = CoinNewsFetcher()
        self.defillama = LlamaChainFetcher(coingecko_base_url=COINGECKO_BASE_URL,
                                           coingecko_headers=COINGECKO_HEADERS)
        self.coins_fetcher = CoinGeckoAPI(coingecko_headers=COINGECKO_HEADERS,
                                          coingecko_base_url=COINGECKO_BASE_URL)
        self.db_session = Session()
        print("OpenAIAssistantManager initialized successfully.")

    def retrieve_assistant(self, assistant_id):
        print(f"Retrieving assistant with ID: {assistant_id}")
        assistant = self.client.beta.assistants.retrieve(assistant_id=assistant_id)
        print(f"Assistant retrieved: {assistant.name}")
        return assistant

    def ensure_thread(self):
        if not self.thread:
            print("Creating new thread...")
            self.thread = self.client.beta.threads.create()
            print(f"New thread created with ID: {self.thread.id}")
        else:
            print(f"Using existing thread with ID: {self.thread.id}")
        return self.thread

    def create_and_save_thread(self, user_id):
        thread = self.ensure_thread()
        db_thread = Thread(
            id=thread.id,
            user_id=user_id,
        )
        self.db_session.add(db_thread)
        self.db_session.commit()
        return db_thread

    def add_message(self, content, role="user"):
        print(f"Adding message to thread. Role: {role}, Content: {content[:50]}...")
        thread = self.ensure_thread()
        message = self.client.beta.threads.messages.create(
            thread_id=thread.id,
            role=role,
            content=content
        )
        
        # Save message to database
        db_message = Message(
            id=message.id,
            thread_id=thread.id,
            role=role,
            content=content
        )
        self.db_session.add(db_message)
        self.db_session.commit()

        print(f"Message added successfully. Message ID: {message.id}")
        return message

    def update_message_feedback(self, message_id: str, feedback: bool):
        db_message = self.db_session.query(Message).filter_by(id=message_id).first()
        if db_message:
            db_message.feedback = feedback
            self.db_session.commit()
            print(f"Updated feedback for message {message_id}")
        else:
            print(f"Message {message_id} not found in database")

    def run_assistant(self, assistant_id):
        print(f"Running assistant with ID: {assistant_id}")
        thread = self.ensure_thread()
        run = self.client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant_id
        )
        print(f"Assistant run created. Run ID: {run.id}")
        return run

    def get_run_status(self, run_id):
        thread = self.ensure_thread()
        run = self.client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run_id
        )
        print(f"Run status for Run ID {run_id}: {run.status}")
        return run.status

    def get_messages(self):
        print("Retrieving messages from thread...")
        thread = self.ensure_thread()
        messages = self.client.beta.threads.messages.list(thread_id=thread.id)
        print(f"Retrieved {len(messages.data)} messages.")
        return messages

    def wait_for_completion(self, run_id, timeout=300):
        print(f"Waiting for run completion. Run ID: {run_id}, Timeout: {timeout}s")
        start_time = time.time()
        while True:
            status = self.get_run_status(run_id)
            elapsed_time = time.time() - start_time
            if status == "completed":
                print(f"Run completed successfully. Total time: {elapsed_time:.2f}s")
                return True
            elif status == "requires_action":
                print(f"Run requires action. Elapsed time: {elapsed_time:.2f}s")
                return "requires_action"
            elif status in ["failed", "cancelled", "expired"]:
                print(f"Run ended with status: {status}. Total time: {elapsed_time:.2f}s")
                return False
            elif status == "cancelling":
                print(f"Run is being cancelled. Elapsed time: {elapsed_time:.2f}s")
            elif status == "in_progress":
                print(f"Run is in progress. Elapsed time: {elapsed_time:.2f}s")
            elif status == "queued":
                print(f"Run is queued. Elapsed time: {elapsed_time:.2f}s")
            elif status == "incomplete":
                print(f"Run ended incomplete. Total time: {elapsed_time:.2f}s")
                return False
            else:
                print(f"Unknown status: {status}. Elapsed time: {elapsed_time:.2f}s")
            if elapsed_time > timeout:
                print(f"Run timed out after {timeout}s")
                raise TimeoutError("Run did not complete within the specified timeout.")
            time.sleep(1)

    def get_assistant_response(self):
        print("Retrieving assistant's response...")
        messages = self.get_messages()
        for message in messages.data:
            if message.role == "assistant":
                response = message.content[0].text.value
                print(f"Assistant response found: {response[:50]}...")
                return response
        print("No assistant response found.")
        return None

    def _process_tool_calls(self, tool_calls: List[Any]) -> List[Dict[str, str]]:
        print(f"Processing {len(tool_calls)} tool calls...")
        tool_outputs = []
        for tool in tool_calls:
            print(f"Processing tool: {tool.function.name}")
            if tool.function.name in ["get_token_data", "get_latest_news", "extract_data", "get_llama_chains"]:
                args = json.loads(tool.function.arguments)
                arg_value = args.get('coin')
                url = args.get('url')
                token_id = args.get('token_id')
                print(f'Tool: {tool.function.name}, Argument: {arg_value or url or token_id}')
                output = None
                if tool.function.name == 'get_token_data':
                    output = self.coins_fetcher.get_token_data(arg_value)
                elif tool.function.name == 'get_latest_news':
                    output = self.news_fetcher.get_latest_news(arg_value)
                elif tool.function.name == 'extract_data':
                    output = self.scraper.extract_data(url)
                elif tool.function.name == 'get_llama_chains':
                    output = self.defillama.get_llama_chains(token_id)
                tool_outputs.append({
                    "tool_call_id": tool.id,
                    "output": str(output)
                })
                print(f"Tool output generated. Length: {len(str(output))}")
            else:
                print(f"Unknown tool: {tool.function.name}")
        print(f"Processed {len(tool_outputs)} tool outputs.")
        return tool_outputs

    def interact_with_assistant(self, assistant_id, user_message, user_id):
        print(f"Starting interaction with assistant. User message: {user_message[:50]}...")
        
        # Create and save thread if it doesn't exist
        if not self.thread:
            self.create_and_save_thread(user_id)
        
        # Add user message
        self.add_message(user_message, role="user")
        
        run = self.run_assistant(assistant_id)
        completion_status = self.wait_for_completion(run.id)
        
        if completion_status == True:
            print("Run completed. Retrieving final assistant response.")
            assistant_response = self.get_assistant_response()
            
            # Save assistant response
            if assistant_response:
                self.add_message(assistant_response, role="assistant")
            
            return assistant_response
        elif completion_status == "requires_action":
            print("Run requires action. Processing tool calls...")
            run = self.client.beta.threads.runs.retrieve(thread_id=self.thread.id, run_id=run.id)
            if hasattr(run, 'required_action') and hasattr(run.required_action, 'submit_tool_outputs'):
                tool_outputs = self._process_tool_calls(run.required_action.submit_tool_outputs.tool_calls)
                if tool_outputs:
                    print("Submitting tool outputs...")
                    second_run = self.client.beta.threads.runs.submit_tool_outputs(
                        thread_id=self.thread.id,
                        run_id=run.id,
                        tool_outputs=tool_outputs
                    )
                    if self.wait_for_completion(second_run.id):
                        print("Second run completed. Retrieving final response.")
                        assistat_response_with_tool_calls = self.get_assistant_response()
                        
                        # Save assistant response
                        if assistat_response_with_tool_calls:
                            self.add_message(assistat_response_with_tool_calls, role="assistant")

                        return assistat_response_with_tool_calls
                    else:
                        print(f"Second run failed or was cancelled.")
                else:
                    print("No tool outputs to submit.")
            else:
                print("No tool calls required or `submit_tool_outputs` not found.")
        else:
            print("Run failed, was cancelled, or ended incomplete.")
        return "Failed to get a response from the assistant."

    def reset_thread(self):
        print("Resetting thread...")
        if self.thread:
            # Mark the thread as inactive in the database
            db_thread = self.db_session.query(Thread).filter_by(id=self.thread.id).first()
            if db_thread:
                db_thread.is_active = False
                self.db_session.commit()
        self.thread = None
        print("Thread reset complete.")

# Initialize the assistant manager
api_key = os.getenv("OPENAI_API_KEY")
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
COINGECKO_HEADERS = {
    "accept": "application/json",
    "x-cg-pro-api-key": COINGECKO_API_KEY,
}

penelope_manager = OpenAIAssistantManager(api_key, COINGECKO_HEADERS, COINGECKO_BASE_URL)







