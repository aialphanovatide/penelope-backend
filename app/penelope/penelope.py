

"""
Penelope class for getting user messages, storing them, and generating responses from multiple AI services,
it can also handle file uploads and annotations in the messages, responds to multiple users and threads,
and can handle tool calls to external APIs.
"""
# Standard library imports
import os
import time
import json
import uuid
from datetime import datetime
from typing import Any, Dict, Generator, List, Tuple, Union, Literal

# Third-party imports
import graphviz
from openai import OpenAI, OpenAIError
from typing_extensions import override
from openai.types.beta.threads.annotation import Annotation
from openai.types.beta.threads.message import Message
from openai import AssistantEventHandler
from openai.types.beta.threads import Text, TextDelta
from openai.types.beta.threads.runs import ToolCall, ToolCallDelta
from openai.types.beta.threads.message_create_params import Attachment
from openai.types.beta.threads.message import Message as OpenAIMessage
from openai.types.beta.assistant_stream_event import (
    # Thread events
    ThreadCreated,
    
    # Thread Run events
    ThreadRunCreated, ThreadRunInProgress, ThreadRunQueued,
    ThreadRunCompleted, ThreadRunFailed, ThreadRunCancelled,
    ThreadRunCancelling, ThreadRunExpired, ThreadRunRequiresAction,
    ThreadRunIncomplete,
    
    # Thread Run Step events
    ThreadRunStepCreated, ThreadRunStepInProgress, ThreadRunStepDelta,
    ThreadRunStepCompleted, ThreadRunStepFailed, ThreadRunStepCancelled,
    ThreadRunStepExpired,
    
    # Thread Message events
    ThreadMessageCreated,
    ThreadMessageCompleted, ThreadMessageInProgress, ThreadMessageIncomplete,
    ThreadMessageDelta
    
)
from werkzeug.datastructures import FileStorage
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from contextlib import contextmanager

# Local application imports
from app.utils.response_template import method_response_template, penelope_response_template
from app.services.scrapper.scrapper import Scraper
from app.services.coingecko.coingecko import CoinGeckoAPI
from app.services.news_bot.news_bot import CoinNewsFetcher
from app.penelope.vector_store_module.vector_store import VectorStoreManager
from app.services.defillama.defillama import LlamaChainFetcher
from app.penelope.assistant_module.assistant import AssistantManager
from app.services.perplexity.perplexity import PerplexityAPI
from app.services.openai_chat.openai import ChatGPTAPI
from app.services.gemini.gemini import GeminiAPI
from config import Message, Thread, Session, File



class Penelope:
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self._log("Initializing OpenAIAssistantManager...")
        
        self._initialize_api_keys()
        self._initialize_clients()
        self._initialize_services()
        self._initialize_tool_functions()
        
        self._log("OpenAIAssistantManager initialized successfully.")

    def _initialize_api_keys(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.coingecko_api_key = os.getenv("COINGECKO_API_KEY")
        self.assistant_id = os.getenv("PENELOPE_ASSISTANT_ID")
        
        if not self.api_key or not self.coingecko_api_key or not self.assistant_id:
            raise ValueError("OPENAI_API_KEY, COINGECKO_API_KEY and PENELOPE_ASSISTANT_ID must be set in the environment.")
        
        self.coingecko_headers = {
            "accept": "application/json",
            "x-cg-pro-api-key": self.coingecko_api_key,
        }

    def _initialize_clients(self):
        self.client = OpenAI(api_key=self.api_key)
        self.coingecko_base_url = "https://pro-api.coingecko.com/api/v3"

    def _initialize_services(self):
        self.threads = {}
        self.queue = []
        self.vector_store = VectorStoreManager(api_key=self.api_key)
        self.scraper = Scraper()
        self.assistant_manager = AssistantManager(api_key=self.api_key)
        self.gemini = GeminiAPI(verbose=self.verbose)
        self.perplexity = PerplexityAPI(verbose=self.verbose)
        self.chatgpt = ChatGPTAPI(verbose=self.verbose)
        self.news_fetcher = CoinNewsFetcher()
        self.defillama = LlamaChainFetcher(coingecko_base_url=self.coingecko_base_url, coingecko_headers=self.coingecko_headers)
        self.coingecko = CoinGeckoAPI(coingecko_headers=self.coingecko_headers, coingecko_base_url=self.coingecko_base_url, verbose=True)

    def _initialize_tool_functions(self):
        self.tool_functions = {
            "get_token_data": self.coingecko.get_token_data,
            "get_latest_news": self.news_fetcher.get_latest_news,
            "extract_data": self.scraper.extract_data,
            "get_llama_chains": self.defillama.get_llama_chains,
            "get_coin_history": self.coingecko.get_coin_history
        }

    @contextmanager
    def get_db_session(self):
        session = Session()
        self._log("Database session opened")
        try:
            yield session
            session.commit()
            self._log("Database changes committed")
        except SQLAlchemyError as e:
            session.rollback()
            self._log(f"Database error, rolling back: {str(e)}")
            raise
        except Exception as e:
            session.rollback()
            self._log(f"Unexpected error, rolling back: {str(e)}")
            raise
        finally:
            session.close()
            self._log("Database session closed")

    @property
    def system_prompt(self):
        return """
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
    
    def _log(self, message: str):
        """
        Log a message if verbose mode is enabled.

        Args:
            message (str): The message to be logged.
        """
        if self.verbose:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}]-{message}\n")
    
    def get_or_create_thread(self, user_id: str) -> Dict[str, Any]:
        """
        Get an existing active thread for the user or create a new one if none exists.

        This method checks for an active thread associated with the given user ID.
        If an active thread is found, it returns that thread's ID. If no active
        thread exists, it creates a new thread for the user.

        Args:
            user_id (str): The unique identifier of the user.

        Returns:
            Dict[str, Any]: A dictionary containing:
                - 'message': A string describing the result of the operation.
                - 'data': The thread ID if successful, None otherwise.
                - 'success': A boolean indicating whether the operation was successful.

        Raises:
            SQLAlchemyError: If there's an issue with database operations.
            Exception: For any other unexpected errors.
        """
        if not user_id:
            return method_response_template(
                message="User ID cannot be None or empty",
                data=None,
                success=False
            )
        
        try:
            with self.get_db_session() as db:
                # Check for an active thread for the user
                active_thread = db.query(Thread).filter_by(user_id=user_id, is_active=True).first()

                if not active_thread:
                    return self.create_new_thread(user_id)
            
                self._log(f"Using existing active thread with ID: {active_thread.id} for user with ID: {user_id}")

                return method_response_template(
                    message="Using existing active thread",
                    data={'thread_id': active_thread.id},
                    success=True
                )

        except SQLAlchemyError as e:
            error_msg = f"Database error creating thread: {str(e)}"
            self._log(error_msg)
            return method_response_template(
                message=error_msg,
                data=None,
                success=False
            )

        except Exception as e:
            error_msg = f"Unexpected error creating thread: {str(e)}"
            self._log(error_msg)
            return method_response_template(
                message=error_msg,
                data=None,
                success=False
            )

    def create_new_thread(self, user_id: str) -> Dict[str, Any]:
        """
        Create a new thread for the given user.

        This method deactivates existing threads for the user (either all or only active ones),
        creates a new thread in OpenAI, and saves it to the database.

        Args:
            user_id (str): The ID of the user for whom to create the thread.
            deactivate_all (bool): If True, deactivate all existing threads. If False, only deactivate active ones.

        Returns:
            Dict[str, Any]: A dictionary containing:
                - 'message': A string describing the result of the operation.
                - 'data': The new thread ID if successful, None otherwise.
                - 'success': A boolean indicating whether the operation was successful.
        """
        self._log(f"Preparing to create new thread for user with ID: {user_id}")

        try:
            with self.get_db_session() as db:
                active_threads = db.query(Thread).filter_by(user_id=user_id, is_active=True).all()
                for thread in active_threads:
                    thread.is_active = False

                # Create the OpenAI thread
                openai_thread = self.client.beta.threads.create()
                thread_id = openai_thread.id

                # Save new thread to database
                new_thread = Thread(id=thread_id, 
                                    user_id=user_id, 
                                    is_active=True,
                                    created_at=datetime.now(),
                                    updated_at=datetime.now()
                                    )
                db.add(new_thread)

                self._log(f"New thread created with ID: {thread_id}")
                return method_response_template(
                    message="New thread created successfully",
                    data={'thread_id': thread_id},
                    success=True
                )

        except (OpenAIError, SQLAlchemyError) as e:
            error_msg = f"Error creating new thread: {str(e)}"
            self._log(error_msg)
            return method_response_template(
                message=error_msg,
                data=None,
                success=False
            )
        except Exception as e:
            error_msg = f"Unexpected error creating new thread: {str(e)}"
            self._log(error_msg)
            return method_response_template(
                message=error_msg,
                data=None,
                success=False
            )
        
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

    def process_annotations(self, chunk: str, thread_id: str) -> str:
        self._log(f"Processing annotations for chunk: {chunk[:50]}...")
        
        # Retrieve the latest message (which should be the one we're currently processing)
        messages = self.get_thread_messages(thread_id)
        print('messages: ', messages)
        if not messages.data:
            self._log("No messages found in the thread.")
            return chunk
        
        latest_message = messages.data[0]
        message_content = latest_message.content[0].text
        annotations = message_content.annotations
        
        if not annotations:
            self._log("No annotations found in the message.")
            return chunk
        
        # Process annotations
        for index, annotation in enumerate(annotations):
            if annotation.text in chunk:
                if (file_citation := getattr(annotation, 'file_citation', None)):
                    try:
                        cited_file = self.client.files.retrieve(file_citation.file_id)
                        chunk = chunk.replace(annotation.text, f' [{index}]')
                        chunk += f'\n[{index}] {file_citation.quote} from {cited_file.filename}'
                    except Exception as e:
                        self._log(f"Error retrieving file citation: {str(e)}")
                elif (file_path := getattr(annotation, 'file_path', None)):
                    try:
                        cited_file = self.client.files.retrieve(file_path.file_id)
                        chunk = chunk.replace(annotation.text, f' [{index}]')
                        chunk += f'\n[{index}] Click <here> to download {cited_file.filename}'
                    except Exception as e:
                        self._log(f"Error retrieving file path: {str(e)}")
        
        self._log(f"Processed chunk with annotations: {chunk[:50]}...")
        return chunk

    def generate_penelope_response_streaming(self, user_message: str, user_id: str, user_name: str, files=None, thread_id: str = None) -> Generator[Dict[str, Any], None, None]:
        
        self._log(f"Starting streaming interaction with assistant for user with ID: {user_name}")
        self._log(f"User message: {user_message[:50]}...")
        
        try:
            # Get or create thread
            if thread_id and thread_id != 'null':
                active_thread_id = thread_id
            else:
                thread_result = self.get_or_create_thread(user_id)
                if not thread_result['success']:
                    yield penelope_response_template(
                        message=f"{thread_result['message']}",
                        id=str(uuid.uuid4()),
                        type='error'
                    )
                    return
                
                active_thread_id = thread_result['data']['thread_id']
                yield penelope_response_template(
                    message=f"Thread created successfully", 
                    id=active_thread_id,
                    type='thread_created'
                )

        
            # Add user message
            user_message_id = str(uuid.uuid4())
            user_message_result = self.add_message(
                content=user_message, 
                role="user", 
                user_id=user_id,
                thread_id=active_thread_id, 
                message_id=user_message_id, 
                files=files
            )
            if not user_message_result['success']:
                yield penelope_response_template(
                    message=f"Error adding message: {user_message_result['message']}", 
                    id=user_message_id,
                    type='error'
                )
                return
            
         
            # Create run and stream response
            full_response = ""
            run_id = None
            for chunk in self.create_run_and_stream_response(thread_id=active_thread_id, 
                                                             user_name=user_name):
                # self._log(f"Chunk: {chunk}")
                full_response += chunk.get('message')
                run_id = chunk.get('id')
                yield chunk

            # Save the assistant response
            if full_response:
                self._log(f"Saving assistant response: {full_response[:50]}...")
                message_result = self.add_message(message_id=run_id, 
                                                  content=full_response, 
                                                  role="penelope_assistant", 
                                                  user_id=None,
                                                  thread_id=active_thread_id)
                if not message_result['success']:
                    yield penelope_response_template(
                        message=f"Error saving assistant response: {message_result['message']}",
                        id=run_id,
                        type='error'
                    )
                    return
                
            self._log("Streaming response completed.")

        except OpenAIError as e:
            error_message = f"OpenAI API error: {str(e)}"
            self._log(error_message)
            yield penelope_response_template(
                message=error_message,
                id=run_id,
                type='error'
            )
        except SQLAlchemyError as e:
            error_message = f"Database error: {str(e)}"
            self._log(error_message)
            yield penelope_response_template(
                message=error_message,
                id=run_id,
                type='error'
            )
        except Exception as e:
            error_message = f"Unexpected error: {str(e)}"
            self._log(error_message)
            yield penelope_response_template(
                message=error_message,
                id=run_id,
                type='error'
            )

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

    def add_message(self, content: str, message_id: str, role: str = "user", thread_id: str = None, user_id: str = None, files: List[str] = None) -> Dict[str, Any]:
        """
        Add a message to a thread and save it to the database.

        Args:
            content (str): The content of the message.
            message_id (str): The unique identifier for the message.
            role (str): The role of the message sender (default: "user").
            thread_id (str): The unique identifier of the thread (default: None).
            files (list): List of file objects to attach to the message.

        Returns:
            Dict[str, Any]: A dictionary containing the response from the OpenAI API.
        """
        self._log(f"Adding message to thread: {thread_id}. Role: {role}, Content: {content[:50]}...")
        
        if not thread_id:
            raise ValueError("thread_id is required to add a message")
        
        openai_role = 'assistant' if '_' in role else 'user'
        timestamp = datetime.now()


        with self.get_db_session() as db_session:
            try:
                # Save message to database using the get_db_session context manager
                db_message = Message(
                    id=message_id,
                    thread_id=thread_id,
                    role=role,
                    content=content,
                    created_at=timestamp,
                    updated_at=timestamp
                )
                db_session.add(db_message)
                db_session.commit()
                self._log(f'Message {message_id} saved to database with timestamp: {timestamp}')


                # Prepare attachments if files are provided
                if files and user_id:
                    self.handle_file_uploads(files=files,
                                                        user_id=user_id,
                                                        thread_id=thread_id,
                                                        message_id=message_id
                                                        )
                  

                # Create message in OpenAI
                self.client.beta.threads.messages.create(
                    thread_id=thread_id,
                    role=openai_role,
                    content=content,
                )

                self._log(f"Message added successfully, Message ID: {db_message.id}")

                return method_response_template(
                    message="Message added successfully",
                    data=message_id,
                    success=True
                )
            except OpenAIError as e:
                self._log(f"OpenAI API error in add_message: {str(e)}")
                db_session.rollback()
                return method_response_template(
                    message=f"OpenAI API error: {str(e)}",
                    data=None,
                    success=False
                )
            except SQLAlchemyError as e:
                self._log(f"Database error in add_message: {str(e)}")
                db_session.rollback()
                return method_response_template(
                    message=f"Database error: {str(e)}",
                    data=None,
                    success=False
                )
            except Exception as e:
                self._log(f"Unexpected error in add_message: {str(e)}")
                db_session.rollback()
                return method_response_template(
                    message=f"Unexpected error: {str(e)}",
                    data=None,
                    success=False
                )
    
    def get_thread_messages(self, thread_id: str) -> Dict[str, Any]:
            """
            Retrieve messages from a thread.

            Args:
                thread_id (str): The unique identifier of the thread.

            Returns:
                Dict[str, Any]: A dictionary containing the method response with keys:
                    - 'message': A string describing the result of the operation.
                    - 'data': The list of messages if successful, None otherwise.
                    - 'success': A boolean indicating whether the operation was successful.

            Raises:
                OpenAIError: If there's an issue with the OpenAI API request.
                ValueError: If the thread_id is invalid.
            """
            try:
                self._log(f"Retrieving messages from thread {thread_id}...")
                messages = self.client.beta.threads.messages.list(thread_id=thread_id)
                self._log(f"Retrieved {len(messages.data)} messages.")
                return method_response_template(
                    message=f"Successfully retrieved {len(messages.data)} messages from thread {thread_id}.",
                    data=messages,
                    success=True
                )
            except OpenAIError as e:
                error_msg = f"Error retrieving messages: {str(e)}"
                self._log(error_msg)
                return method_response_template(
                    message=error_msg,
                    data=None,
                    success=False
                )
            except ValueError as e:
                error_msg = f"Invalid thread_id: {str(e)}"
                self._log(error_msg)
                return method_response_template(
                    message=error_msg,
                    data=None,
                    success=False
                )
            except Exception as e:
                error_msg = f"Unexpected error in get_thread_messages: {str(e)}"
                self._log(error_msg)
                return method_response_template(
                    message=error_msg,
                    data=None,
                    success=False
                )

    def update_message_feedback(self, message_id: str, feedback: str) -> Dict[str, Any]:
        """
        Update the feedback for a specific message in the database.

        Args:
            message_id (str): The unique identifier of the message.
            feedback (str): The feedback to be added or updated.

        Returns:
            Dict[str, Any]: A dictionary containing the method response with keys:
                - 'message': A string describing the result of the operation.
                - 'data': The updated feedback if successful, None otherwise.
                - 'success': A boolean indicating whether the operation was successful.
        """
        self._log(f"Updating feedback for message {message_id}")
        
        try:
            with self.get_db_session() as db_session:
                db_message = db_session.query(Message).filter_by(id=message_id).first()
                if db_message:
                    db_message.feedback = feedback
                    self._log(f"Updated feedback for message {message_id}: {feedback}")
                    return method_response_template(
                        message=f"Successfully updated feedback for message {message_id}",
                        data=feedback,
                        success=True
                    )
                else:
                    self._log(f"Message {message_id} not found in database")
                    return method_response_template(       
                        message=f"Message {message_id} not found in database",
                        data=None,
                        success=False
                    )
        except SQLAlchemyError as e:
            error_msg = f"Database error while updating message feedback: {str(e)}"
            self._log(error_msg)
            return method_response_template(
                message=error_msg,
                data=None,
                success=False
            )
        except Exception as e:
            error_msg = f"Unexpected error while updating message feedback: {str(e)}"
            self._log(error_msg)
            return method_response_template(
                message=error_msg,
                data=None,
                success=False
            )

    def create_run_and_stream_response(self, user_name: str, thread_id: str) -> Generator[Dict[str, Any], None, None]:
        """
        Create an assistant run with the given ID for the specified thread and stream the response.

        Args:
            assistant_id (str): The ID of the assistant to run.
            user_name (str): The name of the user for personalization.
            thread_id (str): The ID of the thread to run the assistant on.

        Yields:
            Dict[str, Any]: Events from the assistant run stream.
        """
        self._log(f"Creating run for thread: {thread_id}")
        assistant_run_id = str(uuid.uuid4())

        try:
            run = self.client.beta.threads.runs.create(
                thread_id=thread_id,
                stream=True,
                # tool_choice = {"type": "function", "function": {"name": "get_latest_news"}},
                parallel_tool_calls=True,
                assistant_id=self.assistant_id,
                additional_instructions=f"If the user is greeting or it's the initial conversation, personalize the response message with the user name, which is: {user_name}.",
            ) 
    
            self._log(f"Assistant run created successfully")

            def process_run_events(run):
                for event in run:
                    if isinstance(event, ThreadCreated):
                        self._log(f"Thread created with ID: {event.data.id}")
                        if event.data.id:
                            assistant_run_id = event.data.id
                    elif isinstance(event, ThreadRunCreated):
                        self._log(f"Thread run created with ID: {event.data.status}")
                    elif isinstance(event, ThreadRunInProgress):
                        self._log(f"Thread run in progress with status: {event.data.status}")
                    elif isinstance(event, ThreadRunQueued):
                        self._log(f"Thread run queued with status: {event.data.status}")
                    elif isinstance(event, ThreadRunCompleted):
                        self._log(f"Thread run completed with status: {event.data.status}")
                    elif isinstance(event, ThreadRunFailed):
                        self._log(f"Thread run failed with status: {event.data.status}")
                        yield penelope_response_template(
                            message=f"Thread run failed with status: {event.data.status}",
                            id=assistant_run_id,
                            type='error'
                        )
                        continue
                    elif isinstance(event, ThreadRunCancelled):
                        self._log(f"Thread run cancelled with status: {event.data.status}")
                    elif isinstance(event, ThreadRunCancelling):
                        self._log(f"Thread run cancelling with status: {event.data.status}")
                    elif isinstance(event, ThreadRunExpired):
                        self._log(f"Thread run expired with status: {event.data.status}")
                        yield penelope_response_template(
                            message=f"Thread run expired with status: {event.data.status}",
                            id=event.data.id,
                            type='error'
                        )
                        continue
                    elif isinstance(event, ThreadRunRequiresAction):
                        self._log(f"Thread run requires action with status: {event.data.status}")
                    
                        tool_outputs = self._process_tool_calls(event.data.required_action.
                        submit_tool_outputs.tool_calls)
                        self._log(f"Tool outputs: {tool_outputs}")
                        if tool_outputs:
                            self._log("Submitting tool outputs...")
                            second_run = self.client.beta.threads.runs.submit_tool_outputs(
                                thread_id=thread_id,
                                run_id=event.data.id,
                                tool_outputs=tool_outputs,
                                stream=True
                            )
                            yield from process_run_events(second_run)
                            self._log("--- Processed second run ---")
                        else:
                            self._log("No tool outputs to submit.")
                            yield penelope_response_template(
                                message="No tool outputs to submit.",
                                id=event.data.id,
                                type='error'
                            )
                            continue
                    elif isinstance(event, ThreadRunIncomplete):
                        self._log(f"Thread run incomplete with status: {event.data.status}")
                        continue
                    elif isinstance(event, ThreadRunStepCreated):
                        self._log(f"Thread run step created with status: {event.data.status}")
                        continue
                    elif isinstance(event, ThreadRunStepInProgress):
                        self._log(f"Thread run step in progress with status: {event.data.status}")
                        continue
                    elif isinstance(event, ThreadRunStepDelta):
                        self._log(f"Thread run step delta with status: {event.data.id}")
                    elif isinstance(event, ThreadRunStepCompleted):
                        self._log(f"Thread run step completed with status: {event.data.status}")
                    elif isinstance(event, ThreadRunStepFailed):
                        self._log(f"Thread run step failed with status: {event.data.status}")
                        yield penelope_response_template(
                            message=f"Thread run step failed with status: {event.data.status}",
                            id=event.data.id,
                            type='error'
                        )
                        continue
                    elif isinstance(event, ThreadRunStepCancelled):
                        self._log(f"Thread run step cancelled with status: {event.data.status}")
                        yield penelope_response_template(
                            message=f"Thread run step cancelled with status: {event.data.status}",
                                id=event.data.id,
                            type='error'
                        )
                        continue
                    elif isinstance(event, ThreadRunStepExpired):
                        self._log(f"Thread run step expired with status: {event.data.status}")
                        yield penelope_response_template(
                            message=f"Thread run step expired with status: {event.data.status}",
                            id=event.data.id,
                            type='error'
                        )
                        continue
                    elif isinstance(event, ThreadMessageCreated):
                        self._log(f"Thread message created with ID: {event.data.status}")
                    elif isinstance(event, ThreadMessageCompleted):
                        self._log(f"Thread message completed with ID: {event.data.status}")
                    elif isinstance(event, ThreadMessageInProgress):
                        self._log(f"Thread message in progress with ID: {event.data.status}")
                    elif isinstance(event, ThreadMessageIncomplete):
                        self._log(f"Thread message incomplete with ID: {event.data.status}")
                    elif isinstance(event, ThreadMessageDelta):
                        # self._log(f"Thread message delta with ID: {event.data.id}")
                        delta = event.data.delta
                        if delta.content:
                            for content_block in delta.content:
                                if content_block.type == 'text':
                                    chunk = content_block.text.value

                                    yield penelope_response_template(
                                        message=chunk,
                                        id=event.data.id,
                                        type='chunk'
                                    )
            
            yield from process_run_events(run)

        except OpenAIError as e:
            error_msg = f"OpenAI API error in create_run_and_stream_response: {str(e)}"
            self._log(error_msg)
            yield penelope_response_template(
                message=error_msg,
                id=assistant_run_id,
                type='error'
            )
        
        except Exception as e:
            error_msg = f"Unexpected error in create_run_and_stream_response: {str(e)}"
            self._log(error_msg)
            yield penelope_response_template(
                message=error_msg,
                id=assistant_run_id,
                type='error'
            )

    def cancel_run(self, thread_id: str, run_id: str) -> Dict[str, Any]:
        """
        Cancel a run that is currently in progress.

        Args:
            thread_id (str): The ID of the thread containing the run.
            run_id (str): The ID of the run to cancel.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the operation.
        """
        self._log(f"Attempting to cancel run {run_id} in thread {thread_id}")

        try:
            cancelled_run = self.client.beta.threads.runs.cancel(
                thread_id=thread_id,
                run_id=run_id
            )

            self._log(f"Run {run_id} cancelled successfully. New status: {cancelled_run.status}")

            return method_response_template(
                message=f"Run {run_id} cancelled successfully",
                data=cancelled_run,
                success=True
            )

        except OpenAIError as e:
            error_msg = f"OpenAI API error while cancelling run: {str(e)}"
            self._log(error_msg)
            return method_response_template(
                message=error_msg,
                data=None,
                success=False
            )
        except Exception as e:
            error_msg = f"Unexpected error while cancelling run: {str(e)}"
            self._log(error_msg)
            return method_response_template(
                message=error_msg,
                data=None,
                success=False
            )

    def handle_file_uploads(self, files: List[FileStorage], thread_id: str, user_id: str, message_id: str) -> Dict[str, Any]:
        """
        Handle file uploads for the OpenAI Assistant API and local database.

        Args:
        files (List[FileStorage]): List of file objects to upload.
        thread_id (str): The ID of the thread to associate the files with.
        user_id (str): The ID of the user uploading the files.

        Returns:
        Dict[str, Any]: A dictionary containing the result of the operation.
        """
        supported_extensions = [
            'c', 'cs', 'cpp', 'doc', 'docx', 'html', 'java', 'json', 'md', 'pdf', 'php', 
            'pptx', 'py', 'rb', 'tex', 'txt', 'css', 'js', 'sh', 'ts', 'csv', 'jpeg', 
            'jpg', 'gif', 'png', 'tar', 'xlsx', 'xml', 'zip'
        ]
        supported_mime_types = {
            'text/x-c', 'text/x-csharp', 'text/x-c++', 'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/html', 'text/x-java', 'application/json', 'text/markdown',
            'application/pdf', 'text/x-php',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'text/x-python', 'text/x-script.python', 'text/x-ruby', 'text/x-tex',
            'text/plain', 'text/css', 'text/javascript', 'application/x-sh',
            'application/typescript', 'application/csv', 'image/jpeg', 'image/gif',
            'image/png', 'application/x-tar',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/xml', 'text/xml', 'application/zip'
        }

        files_ids = []
        MAX_FILE_SIZE_MB = 512  # OpenAI's maximum file size in MB

        try:
            def get_file_size_mb(file):
                file.seek(0, os.SEEK_END)
                size_bytes = file.tell()
                file.seek(0)  # Reset file pointer
                return size_bytes / (1024 * 1024)  # Convert to MB

            with self.get_db_session() as db:
                for file in files:
                    self._log(f"File name: {file.filename}")
                    file_extension = file.filename.split('.')[-1].lower()
                    self._log(f"File extension: {file_extension}")
                    
                    # Check file size
                    file_size_mb = get_file_size_mb(file.stream)
                    self._log(f'File size: {file_size_mb}')
                    if file_size_mb > MAX_FILE_SIZE_MB:
                        self._log(f"File too large: {file.filename} ({file_size_mb:.2f} MB)")
                        return method_response_template(
                            message=f"File too large: {file.filename} ({file_size_mb:.2f} MB). Maximum allowed size is {MAX_FILE_SIZE_MB} MB.",
                            data=None,
                            success=False
                        )

                    if file_extension not in supported_extensions:
                        self._log(f"Unsupported file type: {file.filename}")
                        return method_response_template(
                            message=f"Unsupported file type: {file.filename}",
                            data=None,
                            success=False
                        )
                    
                    if hasattr(file, 'content_type') and file.content_type not in supported_mime_types:
                        self._log(f"Unsupported MIME type: {file.content_type}")
                        continue

                    try:
                        # Upload to OpenAI
                        file_response = self.client.files.create(file=file.stream, purpose="assistants")
                    
                        if file_response.status == 'processed':
                            openai_file_id = file_response.id
                            files_ids.append(openai_file_id)
                            self._log(f"File uploaded successfully: {file.filename}")
                        else:
                            self._log(f"File upload failed: {file}")
                            return method_response_template(
                                message=f"File upload failed: {file.filename}",
                                data=None,
                                success=False
                            )

                        # Reset file pointer
                        file.stream.seek(0)

                        # Update Thread with file
                        self.client.beta.threads.update(
                            thread_id=thread_id,
                            tool_resources= {"code_interpreter": {"file_ids": files_ids}}
                        )
                        self._log(f'File {file.filename} associated with thread {thread_id}')

                        # Save to database
                        db_file = File(
                            openai_file_id=openai_file_id,
                            filename=file.filename,
                            purpose="Assistant",
                            mime_type=file.content_type,
                            size=int(file_size_mb * 1024 * 1024),  # Convert MB back to bytes for consistency
                            user_id=user_id,
                            thread_id=thread_id,
                            message_id=message_id
                        )
                        db.add(db_file)
                        self._log(f"File {file.filename} saved to database and associated with message {message_id}")

                    except OpenAIError as e:
                        self._log(f"Error uploading file {file.filename} to OpenAI: {str(e)}")
                    except SQLAlchemyError as e:
                        self._log(f"Error saving file {file.filename} to database: {str(e)}")
                    except Exception as e:
                        self._log(f"Unexpected error uploading file {file.filename}: {str(e)}")

            self._log(f"Files uploaded successfully. len: {len(files_ids)}, ids: {files_ids}")
            return method_response_template(
                message=f"Successfully uploaded {len(files_ids)} files",
                data=files_ids,
                success=True
            )

        except Exception as e:
            self._log(f"Error in handle_file_uploads: {str(e)}")
            return method_response_template(
                message=f"Error handling file uploads: {str(e)}",
                data=None,
                success=False
            )

    def generate_flowchart(self, steps: List[Dict[str, str]]) -> str:
        """
        Generate a flowchart based on the provided steps.

        Args:
            steps (List[Dict[str, str]]): A list of dictionaries, each containing:
                - 'id': A unique identifier for the step
                - 'text': The text to display in the flowchart node
                - 'next': The id of the next step (optional)

        Returns:
            str: The path to the generated flowchart image
        """
        dot = graphviz.Digraph(comment='Flowchart')
        dot.attr(rankdir='TB', size='8,8')

        # Add nodes
        for step in steps:
            dot.node(step['id'], step['text'])

        # Add edges
        for step in steps:
            if 'next' in step and step['next']:
                dot.edge(step['id'], step['next'])

        # Generate a unique filename
        filename = f"flowchart_{uuid.uuid4().hex[:8]}"
        file_path = dot.render(filename=filename, directory='./static/flowcharts', format='png', cleanup=True)
        
        self._log(f"Flowchart generated: {file_path}")
        return file_path

    def generate_image(self, prompt: str, size: str = "1024x1024", n: int = 1, style: Literal['vivid', 'natural'] = 'vivid') -> List[str]:
        """
        Generate images based on the given prompt.

        Args:
            prompt (str): The text prompt for image generation.
            size (str): The size of the generated image. Defaults to "1024x1024".
            n (int): The number of images to generate. Defaults to 1.

        Returns:
            List[str]: A list of URLs for the generated images.
        """
        # Generate the image using DALL-E
        response = self.client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            n=n,
            style=style
        )

        return [image.url for image in response.data]
    

penelope_manager = Penelope(verbose=True)
















    # def get_thread_messages(self, thread_id: str) -> Dict[str, Any]:
    #     """
    #     Retrieve messages from a thread.

    #     Args:
    #         thread_id (str): The unique identifier of the thread.

    #     Returns:
    #         Dict[str, Any]: A dictionary containing the method response with keys:
    #             - 'message': A string describing the result of the operation.
    #             - 'data': The list of messages if successful, None otherwise.
    #             - 'success': A boolean indicating whether the operation was successful.

    #     Raises:
    #         OpenAIError: If there's an issue with the OpenAI API request.
    #         ValueError: If the thread_id is invalid.
    #     """
    #     try:
    #         self._log(f"Retrieving messages from thread {thread_id}...")
    #         messages = self.client.beta.threads.messages.list(thread_id=thread_id)
    #         self._log(f"Retrieved {len(messages.data)} messages.")
    #         return method_response_template(
    #             message=f"Successfully retrieved {len(messages.data)} messages from thread {thread_id}.",
    #             data=messages,
    #             success=True
    #         )
    #     except OpenAIError as e:
    #         error_msg = f"Error retrieving messages: {str(e)}"
    #         self._log(error_msg)
    #         return method_response_template(
    #             message=error_msg,
    #             data=None,
    #             success=False
    #         )
    #     except ValueError as e:
    #         error_msg = f"Invalid thread_id: {str(e)}"
    #         self._log(error_msg)
    #         return method_response_template(
    #             message=error_msg,
    #             data=None,
    #             success=False
    #         )
    #     except Exception as e:
    #         error_msg = f"Unexpected error in get_thread_messages: {str(e)}"
    #         self._log(error_msg)
    #         return method_response_template(
    #             message=error_msg,
    #             data=None,
    #             success=False
    #         )
        
    # def get_message(self, message_id: str, thread_id: str) -> Dict[str, Any]:
    #     """
    #     Retrieve a specific message from a thread and process its content and annotations.

    #     This method fetches a message from the OpenAI API, extracts its content,
    #     processes any annotations (such as citations or file references), and
    #     returns the formatted message content along with citation information.

    #     Args:
    #         message_id (str): The ID of the message to retrieve.
    #         thread_id (str): The ID of the thread containing the message.

    #     Returns:
    #         Dict[str, Any]: A dictionary containing the method response with keys:
    #             - 'message': A string describing the result of the operation.
    #             - 'data': The processed message content and additional information.
    #             - 'success': A boolean indicating whether the operation was successful.
    #     """
    #     try:
    #         # Retrieve the message object
    #         message = self.client.beta.threads.messages.retrieve(
    #             thread_id=thread_id,
    #             message_id=message_id
    #         )

    #         # Process the message content
    #         content_parts = []
    #         citations: List[str] = []
    #         file_citations: List[Dict[str, str]] = []
    #         images: List[Dict[str, str]] = []

    #         for content in message.content:
    #             if isinstance(content, MessageContentText):
    #                 text_content = self._process_text_content(content.text)
    #                 content_parts.append(text_content['text'])
    #                 citations.extend(text_content['citations'])
    #                 file_citations.extend(text_content['file_citations'])
    #             elif isinstance(content, MessageContentImageFile):
    #                 images.append({
    #                     "file_id": content.image_file.file_id,
    #                     "filename": f"image_{len(images)}.png"  # You might want to get the actual filename
    #                 })

    #         # Prepare the final content
    #         final_content = ' '.join(content_parts)
    #         if citations:
    #             final_content += '\n\nCitations:\n' + '\n'.join(citations)

    #         processed_message = {
    #             "content": final_content,
    #             "citations": citations,
    #             "file_citations": file_citations,
    #             "images": images
    #         }

    #         return method_response_template(
    #             message="Message retrieved and processed successfully",
    #             data=processed_message,
    #             success=True
    #         )

    #     except OpenAIError as oe:
    #         error_msg = f"OpenAI API error: {str(oe)}"
    #         self._log(error_msg)
    #         return method_response_template(
    #             message=error_msg,
    #             data=None,
    #             success=False
    #         )
    #     except ValueError as ve:
    #         error_msg = f"Invalid message or thread ID: {str(ve)}"
    #         self._log(error_msg)
    #         return method_response_template(
    #             message=error_msg,
    #             data=None,
    #             success=False
    #         )
    #     except Exception as e:
    #         error_msg = f"Unexpected error processing message: {str(e)}"
    #         self._log(error_msg)
    #         return method_response_template(
    #             message=error_msg,
    #             data=None,
    #             success=False
    #         )

    # def _process_text_content(self, text: Text) -> Dict[str, Any]:
    #     """
    #     Process text content and its annotations.

    #     Args:
    #         text (Text): The text content object from the OpenAI API.

    #     Returns:
    #         Dict[str, Any]: A dictionary containing processed text and citation information.
    #     """
    #     processed_text = text.value
    #     citations: List[str] = []
    #     file_citations: List[Dict[str, str]] = []

    #     for index, annotation in enumerate(text.annotations):
    #         # Replace the text with a footnote
    #         processed_text = processed_text.replace(annotation.text, f' [{index}]')
            
    #         if annotation.file_citation:
    #             try:
    #                 cited_file = self.client.files.retrieve(annotation.file_citation.file_id)
    #                 citations.append(f'[{index}] {annotation.file_citation.quote} from {cited_file.filename}')
    #                 file_citations.append({
    #                     "file_id": annotation.file_citation.file_id,
    #                     "quote": annotation.file_citation.quote,
    #                     "filename": cited_file.filename
    #                 })
    #             except Exception as e:
    #                 self._log(f"Error retrieving file citation: {str(e)}")
    #         elif annotation.file_path:
    #             try:
    #                 cited_file = self.client.files.retrieve(annotation.file_path.file_id)
    #                 citations.append(f'[{index}] Click <here> to download {cited_file.filename}')
    #                 file_citations.append({
    #                     "file_id": annotation.file_path.file_id,
    #                     "filename": cited_file.filename
    #                 })
    #             except Exception as e:
    #                 self._log(f"Error retrieving file path: {str(e)}")

    #     return {
    #         "text": processed_text,
    #         "citations": citations,
    #         "file_citations": file_citations
    #     }
    


    

