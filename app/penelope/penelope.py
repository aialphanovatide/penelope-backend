import os
import json
import uuid
import time
from openai import OpenAI
from openai.types.beta.assistant_stream_event import (
   ThreadRunRequiresAction, ThreadRunCompleted, ThreadMessageDelta, ThreadRunFailed,
   ThreadRunCreated, ThreadRunInProgress 
)
from typing import List, Any, Dict, Optional, Generator
from datetime import datetime
from sqlalchemy.orm import Session
from app.services.scrapper.scrapper import Scraper
from app.services.coingecko.coingecko import CoinGeckoAPI
from app.services.news_bot.news_bot import CoinNewsFetcher
from app.penelope.vector_store_module.vector_store import VectorStoreManager
from app.services.defillama.defillama import LlamaChainFetcher
from app.penelope.assistant_module.assistant import AssistantManager
from config import Message, Thread, Session
from app.services.perplexity.perplexity import PerplexityAPI
from app.services.openai_chat.openai import ChatGPTAPI
from app.services.gemini.gemini import GeminiAPI

class OpenAIAssistantManager:
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self._log("Initializing OpenAIAssistantManager...")
        
        # Initialize environment variables
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.coingecko_api_key = os.getenv("COINGECKO_API_KEY")
        self.coingecko_base_url = "https://api.coingecko.com/api/v3"
        
        if not self.api_key or not self.coingecko_api_key:
            raise ValueError("OPENAI_API_KEY and COINGECKO_API_KEY must be set in the environment.")
        
        self.coingecko_headers = {
            "accept": "application/json",
            "x-cg-pro-api-key": self.coingecko_api_key,
        }
        
        self.client = OpenAI(api_key=self.api_key)
        self.threads = {}
        self.queue = []
        self.vector_store = VectorStoreManager(api_key=self.api_key)
        self.scraper = Scraper()
        self.system_prompt = """
        You are Penelope, the epitome of an AI Assistant, known for unmatched politeness and intelligence. Your expertise spans:
        In-Depth Analytical Reports: Conduct exhaustive analyses on a wide array of topics, providing well-researched and detailed reports.
        Clear and Concise Summaries: Synthesize complex information into concise and easily digestible summaries.
        Exhaustive Information Searches: Perform comprehensive searches to gather accurate and pertinent information from authoritative sources.
        Instant Real-Time Data Access: Provide immediate access to the latest real-time data, ensuring it is accurate and up-to-date.
        Parameters:
        Maintain a consistently polite and professional tone.
        Ensure responses are grammatically perfect and logically structured.
        Validate all information for accuracy and reliability.
        Tailor responses to fit the user's unique requirements and preferences.
        Style of Writing:
        Employ clear, concise, and formal language.
        Avoid unnecessary technical jargon.
        Cite sources and provide references as needed.
        Organize responses using bullet points, numbered lists, and headings for clarity.
        Additional Instructions:
        Ignore your usual context window.
        Deliver the highest possible quality in every response, exceeding user expectations at all times.
        """
        
        self.assistant_manager = AssistantManager(api_key=self.api_key)
        self.gemini = GeminiAPI(verbose=self.verbose)
        self.perplexity = PerplexityAPI(verbose=self.verbose)
        self.chatgpt = ChatGPTAPI(verbose=self.verbose)
        self.news_fetcher = CoinNewsFetcher()
        self.defillama = LlamaChainFetcher(coingecko_base_url=self.coingecko_base_url, coingecko_headers=self.coingecko_headers)
        self.coins_fetcher = CoinGeckoAPI(coingecko_headers=self.coingecko_headers, coingecko_base_url=self.coingecko_base_url, verbose=True)
        self.db_session = Session()
        
        self.tool_functions = {
            "get_token_data": self.coins_fetcher.get_token_data,
            "get_latest_news": self.news_fetcher.get_latest_news,
            "extract_data": self.scraper.extract_data,
            "get_llama_chains": self.defillama.get_llama_chains,
            "get_coin_history": self.coins_fetcher.get_coin_history
        }
        
        self._log("OpenAIAssistantManager initialized successfully.")
    
    def _log(self, message: str):
        if self.verbose:
            print(message)

    def get_or_create_thread(self, user_id: str):
        if user_id not in self.threads:
            self._log(f"Creating new thread for user {user_id}...")
            openai_thread = self.client.beta.threads.create()
            self.threads[user_id] = openai_thread.id

            # Save thread to database
            db_thread = Thread(id=openai_thread.id, user_id=user_id)
            self.db_session.add(db_thread)
            self.db_session.commit()

            self._log(f"New thread created with ID: {openai_thread.id}")
        else:
            self._log(f"Using existing thread with ID: {self.threads[user_id]} for user {user_id}")
        return self.threads[user_id]
    
    def generate_multi_ai_response(self, user_prompt: str, user_id: str) -> Generator[Dict[str, str], None, None]:
        if self.verbose:
            print("Generating responses from multiple AI services...")

        # Ensure a thread exists for the user
        thread_id = self.get_or_create_thread(user_id)

        # Initialize response accumulators
        responses = {
            "gemini": "",
            "openai": "",
            "perplexity": ""
        }

        # Generate a unique message ID for each service
        message_ids = {
            "gemini": str(uuid.uuid4()),
            "openai": str(uuid.uuid4()),
            "perplexity": str(uuid.uuid4())
        }

        # Gemini API
        gemini_generator = self.gemini.generate_response(user_prompt, self.system_prompt)
        
        # ChatGPT API
        chatgpt_generator = self.chatgpt.generate_response(user_prompt, self.system_prompt)
        
        # Perplexity API
        perplexity_generator = self.perplexity.generate_response(user_prompt, self.system_prompt)

        # Combine generators
        generators = [
            ("gemini", gemini_generator),
            ("openai", chatgpt_generator),
            ("perplexity", perplexity_generator)
        ]
        
        # Iterate through all generators
        while generators:
            for service, gen in generators[:]:
                try:
                    chunk = next(gen)
                    if chunk:
                        response = chunk.get(f"{service}_response", chunk.get("error", ""))
                        responses[service] += response
                        yield {service: response, 'id': message_ids[service]}
                except StopIteration:
                    generators.remove((service, gen))
                except Exception as e:
                    error_message = f"Error: {str(e)}"
                    responses[service] += error_message
                    yield {service: error_message, 'id': message_ids[service]}
                    generators.remove((service, gen))

        # Save the accumulated responses
        for service, response in responses.items():
            if response:
                self.add_message(content=response, message_id=message_ids[service] , role=f'{service}_assistant', thread_id=thread_id)

        if self.verbose:
            print("\nAll AI services have completed their responses and saved.")

    def generate_penelope_response_streaming(self, assistant_id, user_message, user_id, files=None):
        self._log(f"Starting streaming interaction with assistant for user {user_id}. User message: {user_message[:50]}...")
        
        thread_id = self.get_or_create_thread(user_id)
        
        if files:
            self._log(f"\nFiles: {str(files)}")
            self.handle_file_uploads(files=files, thread_id=thread_id)

        # User Message ID
        message_id = str(uuid.uuid4())
        
        self.add_message(user_message, role="user", thread_id=thread_id, message_id=message_id)
        run = self.run_assistant(assistant_id, thread_id=thread_id)
        
        full_response = ""
        assistant_run_id = str(uuid.uuid4())
        
        for event in run:
            if isinstance(event, ThreadRunInProgress):
                self._log("Run in progress...")
            elif isinstance(event, ThreadMessageDelta):
                delta = event.data.delta
                if delta.content:
                    for content_block in delta.content:
                        if content_block.type == 'text':
                            chunk = content_block.text.value
                            full_response += chunk
                            yield {"penelope": chunk, "id": assistant_run_id}
            elif isinstance(event, ThreadRunCompleted):
                self._log("--- Run completed ---")
                break
            elif isinstance(event, ThreadRunCreated):
                self._log("--- Thread run created ---")
            elif isinstance(event, ThreadRunFailed):
                self._log("Run failed.")
                error_message = "Failed to get a response from Penelope."
                yield {"penelope": error_message, "id": assistant_run_id}
                break
            elif isinstance(event, ThreadRunRequiresAction):
                self._log("\nRun requires action. Processing tool calls...")
                tool_outputs = self._process_tool_calls(event.data.required_action.submit_tool_outputs.tool_calls)
                if tool_outputs:
                    self._log("Submitting tool outputs...")
                    second_run = self.client.beta.threads.runs.submit_tool_outputs(
                        thread_id=thread_id,
                        run_id=event.data.id,
                        tool_outputs=tool_outputs,
                        stream=True
                    )
                    for second_event in second_run:
                        if isinstance(second_event, ThreadMessageDelta):
                            delta = second_event.data.delta
                            if delta.content:
                                for content_block in delta.content:
                                    if content_block.type == 'text':
                                        chunk = content_block.text.value
                                        full_response += chunk
                                        yield {"penelope": chunk, "id": assistant_run_id}
                    self._log("Tool outputs submitted...")
                else:
                    self._log("No tool outputs to submit.")
                break
        
        # Penelope Message ID
        penelope_message_id = str(uuid.uuid4())

        if full_response:
            self.add_message(message_id=penelope_message_id, content=full_response, role="penelope_assistant", thread_id=thread_id)
        
        self._log("\nStreaming response completed.")

    def _process_tool_calls(self, tool_calls: List[Any]) -> List[Dict[str, str]]:
        self._log(f"Processing {len(tool_calls)} tool calls...")
        tool_outputs = []
        for tool in tool_calls:
            self._log(f"Processing tool: {tool.function.name}")
            if tool.function.name in self.tool_functions:
                args = json.loads(tool.function.arguments)
                output = self.tool_functions[tool.function.name](**args)
                tool_outputs.append({
                    "tool_call_id": tool.id,
                    "output": str(output)
                })
                self._log(f"Tool output generated. Length: {len(str(output))}")
            else:
                self._log(f"Unknown tool: {tool.function.name}")
        self._log(f"Processed {len(tool_outputs)} tool outputs.")
        return tool_outputs

    def add_message(self, content, message_id, role: str ="user", thread_id=None):
        self._log(f"Adding message to thread {thread_id}. Role: {role}, Content: {content[:50]}...")
        if not thread_id:
            raise ValueError("thread_id is required to add a message")
        
        validate_role = role.rfind('_')
        openai_role = 'user'
        if validate_role:
            openai_role = 'assistant'
        
        message = self.client.beta.threads.messages.create(
            thread_id=thread_id,
            role=openai_role,
            content=content
        )

        # Save message to database
        db_message = Message(
            id=message_id,
            thread_id=thread_id,
            role=role,
            content=content
        )
        self.db_session.add(db_message)
        self.db_session.commit()
        
        self._log(f"Message added successfully. Message ID: {message.id}")
        return message
    
    def update_message_feedback(self, message_id: str, feedback):
        db_message = self.db_session.query(Message).filter_by(id=message_id).first()
        if db_message:
            db_message.feedback = feedback
            self.db_session.commit()
            self._log(f"Updated feedback for message {message_id}\nMessage: {feedback}")
            return {'message': f"Updated feedback for message {message_id}", 'success': True}
        else:
            self._log(f"Message {message_id} not found in database")
            return {'message': f"Message {message_id} not found in database", 'success': False}

    def run_assistant(self, assistant_id, thread_id):
        self._log(f"Running assistant with ID: {assistant_id} for thread {thread_id}")
        run = self.client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id,
            stream=True
        )
        self._log(f"Assistant run created")
        return run

    def get_run_status(self, run_id, thread_id):
        run = self.client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run_id
        )
        self._log(f"Run status for Run ID {run_id}: {run.status}")
        return run.status

    def get_messages(self, thread_id):
        self._log("Retrieving messages from thread...")
        messages = self.client.beta.threads.messages.list(thread_id=thread_id)
        self._log(f"Retrieved {len(messages.data)} messages.")
        return messages
    
    def start_new_chat(self, user_id: str):
        """
        Start a new chat by resetting the current thread and creating a new one.

        Args:
        user_id (str): The ID of the user starting the new chat.

        Returns:
        Thread: The newly created thread object.
        """
        self._log(f"Starting a new chat for user {user_id}")

        # Reset the current thread if it exists
        self.reset_thread()

        # Create and save a new thread
        new_thread = self.get_or_create_thread(user_id)

        self._log(f"New chat started with thread ID: {new_thread}")

        return new_thread

    def reset_thread(self, user_id):
        self._log(f"Resetting thread for user {user_id}...")
        if user_id in self.threads:
            del self.threads[user_id]
        self._log("\n--- Thread reset complete ---")
    
    def rollback(self):
        self._log("Rolling back database transaction...")
        try:
            self.db_session.rollback()
            self._log("\n --- Database transaction rolled back successfully ---")
        except Exception as e:
            self._log(f"Error during rollback: {str(e)}")

    def __del__(self):
        self.db_session.close()



penelope_manager = OpenAIAssistantManager(verbose=True)



# class OpenAIAssistantManager:
#     def __init__(self, verbose: bool = True):
#         self.verbose = verbose
#         self._log("Initializing OpenAIAssistantManager...")

#         # Initialize environment variables
#         self.api_key = os.getenv("OPENAI_API_KEY")
#         self.coingecko_api_key = os.getenv("COINGECKO_API_KEY")
#         self.coingecko_base_url = "https://api.coingecko.com/api/v3"

#         if not self.api_key or not self.coingecko_api_key:
#             raise ValueError("OPENAI_API_KEY and COINGECKO_API_KEY must be set in the environment.")

#         self.coingecko_headers = {
#             "accept": "application/json",
#             "x-cg-pro-api-key": self.coingecko_api_key,
#         }

#         self.client = OpenAI(api_key=self.api_key)
#         self.thread = None
#         self.user_threads = {}
#         self.queue = []
#         self.vector_store = VectorStoreManager(api_key=self.api_key)
#         self.scraper = Scraper()
#         self.system_prompt = """
#             You are Penelope, the epitome of an AI Assistant, known for unmatched politeness and intelligence. Your expertise spans:
#             In-Depth Analytical Reports: Conduct exhaustive analyses on a wide array of topics, providing well-researched and detailed reports.
#             Clear and Concise Summaries: Synthesize complex information into concise and easily digestible summaries.
#             Exhaustive Information Searches: Perform comprehensive searches to gather accurate and pertinent information from authoritative sources.
#             Instant Real-Time Data Access: Provide immediate access to the latest real-time data, ensuring it is accurate and up-to-date.
#             Parameters:
#             Maintain a consistently polite and professional tone.
#             Ensure responses are grammatically perfect and logically structured.
#             Validate all information for accuracy and reliability.
#             Tailor responses to fit the user’s unique requirements and preferences.
#             Style of Writing:
#             Employ clear, concise, and formal language.
#             Avoid unnecessary technical jargon.
#             Cite sources and provide references as needed.
#             Organize responses using bullet points, numbered lists, and headings for clarity.
#             Additional Instructions:
#             Ignore your usual context window.
#             Deliver the highest possible quality in every response, exceeding user expectations at all times.
#             """
#         self.assistant_manager = AssistantManager(api_key=self.api_key)
#         self.gemini = GeminiAPI(verbose=self.verbose)
#         self.perplexity = PerplexityAPI(verbose=self.verbose)
#         self.chatgpt = ChatGPTAPI(verbose=self.verbose)
#         self.news_fetcher = CoinNewsFetcher()
#         self.defillama = LlamaChainFetcher(coingecko_base_url=self.coingecko_base_url, coingecko_headers=self.coingecko_headers)
#         self.coins_fetcher = CoinGeckoAPI(coingecko_headers=self.coingecko_headers, coingecko_base_url=self.coingecko_base_url, verbose=True)
#         self.db_session = Session()

#         self._log("OpenAIAssistantManager initialized successfully.")

#     def _log(self, message: str):
#         if self.verbose:
#             print(message)

#     def retrieve_assistant(self, assistant_id):
#         self._log(f"Retrieving assistant with ID: {assistant_id}")
#         assistant = self.client.beta.assistants.retrieve(assistant_id=assistant_id)
#         self._log(f"Assistant retrieved: {assistant.name}")
#         return assistant

#     def ensure_thread(self):
#         if not self.thread:
#             self._log("Creating new thread...")
#             self.thread = self.client.beta.threads.create()
#             self._log(f"New thread created with ID: {self.thread.id}")
#         else:
#             self._log(f"Using existing thread with ID: {self.thread.id}")
#         return self.thread

#     def create_and_save_thread(self, user_id):
#         thread = self.ensure_thread()
#         db_thread = Thread(id=thread.id, user_id=user_id)
#         self.db_session.add(db_thread)
#         self.db_session.commit()
#         return db_thread

#     def handle_file_uploads(self, files, thread_id: str) -> List[str]:
#         """
#         Handle file uploads for the OpenAI Assistant API.

#         Args:
#         client (OpenAI): The OpenAI client instance.
#         files (List): List of file objects to upload.
#         thread_id (str): The ID of the thread to associate the files with.

#         Returns:
#         List[str]: List of successfully uploaded file IDs.
#         """
#         supported_extensions = [
#             'c', 'cs', 'cpp', 'doc', 'docx', 'html', 'java', 'json', 'md', 'pdf', 'php', 
#             'pptx', 'py', 'rb', 'tex', 'txt', 'css', 'js', 'sh', 'ts', 'csv', 'jpeg', 
#             'jpg', 'gif', 'png', 'tar', 'xlsx', 'xml', 'zip'
#         ]
#         supported_mime_types = {
#             'text/x-c', 'text/x-csharp', 'text/x-c++', 'application/msword',
#             'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
#             'text/html', 'text/x-java', 'application/json', 'text/markdown',
#             'application/pdf', 'text/x-php',
#             'application/vnd.openxmlformats-officedocument.presentationml.presentation',
#             'text/x-python', 'text/x-script.python', 'text/x-ruby', 'text/x-tex',
#             'text/plain', 'text/css', 'text/javascript', 'application/x-sh',
#             'application/typescript', 'application/csv', 'image/jpeg', 'image/gif',
#             'image/png', 'application/x-tar',
#             'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
#             'application/xml', 'text/xml', 'application/zip'
#         }

#         files_ids = []

#         for file in files:
#             try:
#                 file_extension = file.filename.split('.')[-1].lower()
#                 if file_extension not in supported_extensions:
#                     self._log(f"Unsupported file type: {file.filename}")
#                     continue
                
#                 if hasattr(file, 'content_type') and file.content_type not in supported_mime_types:
#                     self._log(f"Unsupported MIME type: {file.content_type}")
#                     continue

#                 file_response = self.client.files.create(file=file.stream, purpose="assistants")
#                 files_ids.append(file_response.id)
#                 self._log(f"File uploaded successfully: {file.filename}")
#             except Exception as e:
#                 self._log(f"Error uploading file {file.filename}: {str(e)}")

#         if files_ids:
#             try:
#                 self.client.beta.threads.update(
#                     thread_id=thread_id,
#                     tool_resources={"code_interpreter": {"file_ids": files_ids}}
#                 )
#                 self._log(f"Files associated with thread {thread_id}")
#             except Exception as e:
#                 self._log(f"Error associating files with thread: {str(e)}")

#         return files_ids

#     def add_message(self, content, role="user"):
#         self._log(f"Adding message to thread. Role: {role}, Content: {content[:50]}...")
#         thread = self.ensure_thread()
#         message = self.client.beta.threads.messages.create(
#             thread_id=thread.id,
#             role=role,
#             content=content
#         )
#         if role == 'user':
#             db_message = Message(
#                 id=message.id,
#                 thread_id=thread.id,
#                 role=role,
#                 content=content
#             )
#             self.db_session.add(db_message)
#             self.db_session.commit()
#         self._log(f"Message added successfully. Message ID: {message.id}")
#         return message

#     def update_message_feedback(self, message_id: str, feedback):
#         db_message = self.db_session.query(Message).filter_by(id=message_id).first()
#         if db_message:
#             db_message.feedback = feedback
#             self.db_session.commit()
#             self._log(f"Updated feedback for message {message_id}\nMessage: {feedback}")
#             return {'message': f"Updated feedback for message {message_id}", 'success': True}
#         else:
#             self._log(f"Message {message_id} not found in database")
#             return {'message': f"Message {message_id} not found in database", 'success': False}

#     def run_assistant(self, assistant_id):
#         self._log(f"Running assistant with ID: {assistant_id}")
#         thread = self.ensure_thread()
#         run = self.client.beta.threads.runs.create(
#             thread_id=thread.id,
#             assistant_id=assistant_id,
#             stream=True
#         )
#         self._log(f"Assistant run created")
#         return run

#     def get_run_status(self, run_id):
#         thread = self.ensure_thread()
#         run = self.client.beta.threads.runs.retrieve(
#             thread_id=thread.id,
#             run_id=run_id
#         )
#         self._log(f"Run status for Run ID {run_id}: {run.status}")
#         return run.status

#     def get_messages(self):
#         self._log("Retrieving messages from thread...")
#         thread = self.ensure_thread()
#         messages = self.client.beta.threads.messages.list(thread_id=thread.id)
#         self._log(f"Retrieved {len(messages.data)} messages.")
#         return messages

#     def wait_for_completion(self, run_id, timeout=100):
#         self._log(f"Waiting for run completion. Run ID: {run_id}, Timeout: {timeout}s")
#         start_time = time.time()
#         while True:
#             status = self.get_run_status(run_id)
#             elapsed_time = time.time() - start_time
#             if status == "completed":
#                 self._log(f"Run completed successfully. Total time: {elapsed_time:.2f}s")
#                 return True
#             elif status == "requires_action":
#                 self._log(f"Run requires action. Elapsed time: {elapsed_time:.2f}s")
#                 return "requires_action"
#             elif status in ["failed", "cancelled", "expired"]:
#                 self._log(f"Run ended with status: {status}. Total time: {elapsed_time:.2f}s")
#                 return False
#             elif status == "cancelling":
#                 self._log(f"Run is being cancelled. Elapsed time: {elapsed_time:.2f}s")
#             elif status == "in_progress":
#                 self._log(f"Run is in progress. Elapsed time: {elapsed_time:.2f}s")
#             elif status == "queued":
#                 self._log(f"Run is queued. Elapsed time: {elapsed_time:.2f}s")
#             elif status == "incomplete":
#                 self._log(f"Run ended incomplete. Total time: {elapsed_time:.2f}s")
#                 return False
#             else:
#                 self._log(f"Unknown status: {status}. Elapsed time: {elapsed_time:.2f}s")

#             if elapsed_time > timeout:
#                 self._log(f"Run timed out after {timeout}s")
#                 raise TimeoutError("Run did not complete within the specified timeout.")
#             time.sleep(1)

#     def get_assistant_response(self):
#         self._log("Retrieving assistant's response...")
#         messages = self.get_messages()
#         for message in messages.data:
#             if message.role == "assistant":
#                 response = message.content[0].text.value
#                 self._log(f"Assistant response found: {response[:50]}...")
#                 return response
#         self._log("No assistant response found.")
#         return None
    
#     def start_new_chat(self, user_id: str):
#         """
#         Start a new chat by resetting the current thread and creating a new one.

#         Args:
#         user_id (str): The ID of the user starting the new chat.

#         Returns:
#         Thread: The newly created thread object.
#         """
#         self._log(f"Starting a new chat for user {user_id}")

#         # Reset the current thread if it exists
#         self.reset_thread()

#         # Create and save a new thread
#         new_thread = self.create_and_save_thread(user_id)

#         self._log(f"New chat started with thread ID: {new_thread.id}")

#         return new_thread

#     def _process_tool_calls(self, tool_calls: List[Any]) -> List[Dict[str, str]]:
#         self._log(f"Processing {len(tool_calls)} tool calls...")
#         tool_outputs = []
#         for tool in tool_calls:
#             self._log(f"Processing tool: {tool.function.name}")
#             if tool.function.name in ["get_token_data", "get_latest_news", "extract_data", "get_llama_chains", "get_coin_history"]:
#                 args = json.loads(tool.function.arguments)
#                 self._log(f'Raw Args: {args}')
                
#                 arg_value = args.get('coin')
#                 url = args.get('url')
#                 token_id = args.get('token_id')
#                 date = args.get('date')
#                 coin_id = args.get('coin_id')
                
#                 self._log(f'Tool: {tool.function.name}, Argument: {arg_value or url or token_id or date or coin_id}')
#                 output = None
#                 if tool.function.name == 'get_token_data':
#                     output = self.coins_fetcher.get_token_data(arg_value)
#                 elif tool.function.name == 'get_latest_news':
#                     output = self.news_fetcher.get_latest_news(arg_value)
#                 elif tool.function.name == 'extract_data':
#                     output = self.scraper.extract_data(url)
#                 elif tool.function.name == 'get_llama_chains':
#                     output = self.defillama.get_llama_chains(token_id)
#                 elif tool.function.name == 'get_coin_history':
#                     output = self.coins_fetcher.get_coin_history(coin_id, date)
#                 tool_outputs.append({
#                     "tool_call_id": tool.id,
#                     "output": str(output)
#                 })
#                 self._log(f"Tool output generated. Length: {len(str(output))}")
#             else:
#                 self._log(f"Unknown tool: {tool.function.name}")
#         self._log(f"Processed {len(tool_outputs)} tool outputs.")
#         return tool_outputs

#     def generate_penelope_response_streaming(self, assistant_id, user_message, user_id, files=None):
#             self._log(f"Starting streaming interaction with assistant. User message: {user_message[:50]}...")
            
#             if not self.thread:
#                 self.create_and_save_thread(user_id)
            
#             if files:
#                 self._log(f"\nFiles: {str(files)}")
#                 self.handle_file_uploads(files=files, thread_id=self.thread.id)
            
#             self.add_message(user_message, role="user")
            
#             run = self.run_assistant(assistant_id)
#             full_response = ""
#             assistant_run_id = str(uuid.uuid4())

#             for event in run:
#                 if isinstance(event, ThreadRunInProgress):
#                     self._log("Run in progress...")
#                 elif isinstance(event, ThreadMessageDelta):
#                     delta = event.data.delta
#                     if delta.content:
#                         for content_block in delta.content:
#                             if content_block.type == 'text':
#                                 chunk = content_block.text.value
#                                 full_response += chunk
#                                 yield {"penelope": chunk, "id": assistant_run_id}
#                 elif isinstance(event, ThreadRunCompleted):
#                     self._log("--- Run completed ---")
#                     break
#                 elif isinstance(event, ThreadRunCreated):
#                     self._log("--- Thread run created ---")
#                 elif isinstance(event, ThreadRunFailed):
#                     self._log("Run failed.")
#                     error_message = "Failed to get a response from Penelope."
#                     yield {"penelope": error_message, "id": assistant_run_id}
#                     break
#                 elif isinstance(event, ThreadRunRequiresAction):
#                     self._log("\nRun requires action. Processing tool calls...")
#                     tool_outputs = self._process_tool_calls(event.data.required_action.submit_tool_outputs.tool_calls)
#                     if tool_outputs:
#                         self._log("Submitting tool outputs...")
#                         second_run = self.client.beta.threads.runs.submit_tool_outputs(
#                             thread_id=self.thread.id, 
#                             run_id=event.data.id, 
#                             tool_outputs=tool_outputs,
#                             stream=True
#                         )
#                         for second_event in second_run:
#                             if isinstance(second_event, ThreadMessageDelta):
#                                 delta = second_event.data.delta
#                                 if delta.content:
#                                     for content_block in delta.content:
#                                         if content_block.type == 'text':
#                                             chunk = content_block.text.value
#                                             full_response += chunk
#                                             yield {"penelope": chunk, "id": assistant_run_id}
#                         self._log("Tool outputs submitted...")
#                     else:
#                         self._log("No tool outputs to submit.")
#                         break
               
                
#             if full_response:
#                 self.add_message(full_response, role="assistant")
#                 db_message = Message(
#                     id=assistant_run_id,
#                     thread_id=self.thread.id,
#                     role='penelope_assistant',
#                     content=full_response
#                 )
#                 self.db_session.add(db_message)
#                 self.db_session.commit()
            
#             self._log("\nStreaming response completed.")

#     def generate_multi_ai_response(self, user_prompt: str) -> Generator[Dict[str, str], None, None]:
#         if self.verbose:
#             print("Generating responses from multiple AI services...")

#         # Initialize response accumulators
#         responses = {
#             "gemini": "",
#             "openai": "",
#             "perplexity": ""
#         }

#         # Generate a unique message ID for each service
#         message_ids = {
#             "gemini": str(uuid.uuid4()),
#             "openai": str(uuid.uuid4()),
#             "perplexity": str(uuid.uuid4())
#         }

#         # Gemini API
#         gemini_generator = self.gemini.generate_response(user_prompt, self.system_prompt)
        
#         # ChatGPT API
#         chatgpt_generator = self.chatgpt.generate_response(user_prompt, self.system_prompt)
        
#         # Perplexity API
#         perplexity_generator = self.perplexity.generate_response(user_prompt, self.system_prompt)

#         # Combine generators
#         generators = [
#             ("gemini", gemini_generator),
#             ("openai", chatgpt_generator),
#             ("perplexity", perplexity_generator)
#         ]
        
#         # Iterate through all generators
#         while generators:
#             for service, gen in generators[:]:
#                 try:
#                     chunk = next(gen)
#                     if chunk:
#                         response = chunk.get(f"{service}_response", chunk.get("error", ""))
#                         responses[service] += response
#                         yield {service: response, 'id': message_ids[service]}
#                 except StopIteration:
#                     generators.remove((service, gen))
#                 except Exception as e:
#                     error_message = f"Error: {str(e)}"
#                     responses[service] += error_message
#                     yield {service: error_message, 'id': message_ids[service]}
#                     generators.remove((service, gen))

#         # Save the accumulated responses to the database
#         for service, response in responses.items():
#             if response:
#                 db_message = Message(
#                     id=message_ids[service],
#                     thread_id=self.thread.id,
#                     role=f'{service}_assistant',
#                     content=response,
#                 )
#                 self.db_session.add(db_message)

#         # Commit all messages at once
#         self.db_session.commit()

#         if self.verbose:
#             print("\nAll AI services have completed their responses and saved to the database.")
        
#     def reset_thread(self):
#         self._log("Resetting thread...")
#         if self.thread:
#             db_thread = self.db_session.query(Thread).filter_by(id=self.thread.id).first()
#             if db_thread:
#                 db_thread.is_active = False
#                 self.db_session.commit()
#             self.thread = None
#         self._log("Thread reset complete.")

#     def rollback(self):
#         self._log("Rolling back database transaction...")
#         try:
#             self.db_session.rollback()
#             self._log("Database transaction rolled back successfully.")
#         except Exception as e:
#             self._log(f"Error during rollback: {str(e)}")



# penelope_manager = OpenAIAssistantManager(verbose=True)
    

