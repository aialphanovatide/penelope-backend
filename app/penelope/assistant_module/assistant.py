"""
# Assistant module: create, update, delete, list, get assistant details, it is used for the agent to interact with the OpenAI API.
"""

from app.utils.response_template import method_response_template
from typing import List, Dict, Any, Optional
from werkzeug.utils import secure_filename
from openai import OpenAI
import time
import os

class AssistantManager:
    def __init__(self, api_key: Optional[str] = None, verbose: bool = False):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            raise ValueError("OpenAI API key not provided and OPENAI_API_KEY environment variable not set")

        self.client = OpenAI(api_key=self.api_key)
        self.verbose = verbose

    def log_debug(self, message: str, *args, **kwargs):
        if self.verbose:
            print(f"DEBUG: {message}", *args, **kwargs)

    def create_assistant(self, model: str, name: str, instructions: str, 
                         tools: Optional[List[Dict[str, Any]]] = None, 
                         temperature: float = 0.5) -> Dict[str, Any]:
        """
        Create a new assistant with the specified parameters.

        Args:
            model (str): The model to use for the assistant.
            name (str): The name of the assistant.
            instructions (str): The instructions for the assistant.
            tools (Optional[List[Dict[str, Any]]], optional): A list of tools for the assistant. Defaults to None.
            temperature (float, optional): The temperature setting for the assistant. Defaults to 0.5.

        Returns:
            Dict[str, Any]: The created assistant object.

        Raises:
            Exception: If there's an error during assistant creation.
        """
        try:
            assistant = self.client.beta.assistants.create(
                model=model,
                name=name,
                instructions=instructions,
                tools=tools or [],
                temperature=temperature
            )
            return method_response_template(message="Assistant created successfully", 
                                             data=assistant.model_dump(), 
                                             success=True
                                             )
        except Exception as e:
            self.log_debug(f"Error creating assistant: {str(e)}")
            self.log_debug(f"Assistant creation parameters: model={model}, name={name}, instructions={instructions}, tools={tools}, temperature={temperature}")
            return method_response_template(message=f"Failed to create assistant: {str(e)}", 
                                             data={"model": model, "name": name, "instructions": instructions, "tools": tools, "temperature": temperature}, 
                                             success=False
                                             )

    def list_assistants(self, limit: int = 20, order: str = "desc", after: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all assistants, up to the specified limit.

        Args:
            limit (int): The maximum number of assistants to return. Default is 20.
            order (str): The order of the assistants. Can be "asc" or "desc". Default is "desc".
            after (Optional[str]): A cursor for use in pagination. `after` is an object ID that defines your place in the list. Default is None.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each containing the details of an assistant.

        Raises:
            ValueError: If an invalid order is provided.
            Exception: If there's an error during the API call.
        """
        try:
            if order not in ["asc", "desc"]:
                raise ValueError("Invalid order. Must be 'asc' or 'desc'.")

            assistants = self.client.beta.assistants.list(limit=limit, order=order, after=after)
            assistant_list = [assistant.model_dump() for assistant in assistants.data]

            print("len:", len(assistant_list))

            self.log_debug(f"Successfully retrieved {len(assistant_list)} assistants.")
            return method_response_template(message=f"Successfully retrieved {len(assistant_list)} assistants.", 
                                             data=assistant_list, 
                                             success=True
                                             )
        
        except Exception as e:
            self.log_debug(f"Error listing assistants: {str(e)}")
            return method_response_template(message=f"Failed to list assistants: {str(e)}", 
                                             data={"limit": limit, "order": order, "after": after}, 
                                             success=False
                                             )

    def delete_assistant(self, assistant_id: str) -> Dict[str, Any]:
        """
        Delete an assistant by its ID.

        Args:
            assistant_id (str): The ID of the assistant to delete.

        Returns:
            Dict[str, Any]: A dictionary containing the details of the deleted assistant.

        Raises:
            AssistantDeletionError: If there's an error during the deletion process.
        """
        try:
            self.log_debug(f"Attempting to delete assistant with ID: {assistant_id}")
            deleted_assistant = self.client.beta.assistants.delete(assistant_id)
            self.log_debug(f"Successfully deleted assistant with ID: {assistant_id}")
            return method_response_template(message="Successfully deleted assistant", 
                                             data=deleted_assistant.model_dump(), 
                                             success=True
                                             )
        except Exception as e:
            self.log_debug(f"Error deleting assistant with ID {assistant_id}: {str(e)}")
            return method_response_template(message=f"Failed to delete assistant: {str(e)}", 
                                             data={"assistant_id": assistant_id}, 
                                             success=False
                                             )

    def update_assistant(self, assistant_id: str, **kwargs) -> Dict[str, Any]:
        """
        Update an assistant with the provided parameters.

        Args:
            assistant_id (str): The ID of the assistant to update.
            **kwargs: Arbitrary keyword arguments representing the fields to update.
                      These can include 'name', 'description', 'instructions', 'model', 'tools', 'temperature', 'top_p', 'response_format', 'tool_resources', 'metadata'.

        Returns:
            Dict[str, Any]: A dictionary containing the details of the updated assistant.

        Raises:
            AssistantError: If there's an error during the update process.
        """
        try:
            self.log_debug(f"Attempting to update assistant with ID: {assistant_id}")
            updated_assistant = self.client.beta.assistants.update(assistant_id, **kwargs)
            self.log_debug(f"Successfully updated assistant with ID: {assistant_id}")
            return method_response_template(message="Successfully updated assistant", 
                                             data=updated_assistant.model_dump(), 
                                             success=True
                                             )
        except Exception as e:
            self.log_debug(f"Error updating assistant with ID {assistant_id}: {str(e)}")
            return method_response_template(message=f"Failed to update assistant: {str(e)}", 
                                             data={"assistant_id": assistant_id, "details": kwargs}, 
                                             success=False
                                             )
    
    def ask_assistant_with_files(self, assistant_id: str, message: str, files: List[Any] = None) -> Dict[str, Any]:
        try:
            # Step 1: Create a Thread
            thread = self.client.beta.threads.create()
            self.log_debug(f"Creating a thread for assistant with ID: {assistant_id}")

            # Step 2: Upload Files and Get their IDs
            attachments = []
            if files:
                for file in files:
                    filename = secure_filename(file.filename)
                    self.log_debug(f"Uploading file: {filename}")
                    purpose = "vision" if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')) else "assistants"
                    response = self.client.files.create(file=file, purpose=purpose)
                    self.log_debug(f"File response: {response}")
                    attachments.append({"file_id": response.id})

            # Step 3: Add a Message with Attachments to the Thread
            self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=message,
                attachments=attachments
            )
            self.log_debug(f"Adding a message with attachments to the thread: {thread.id}")

            # Step 4: Run the Assistant on the Thread
            run = self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=assistant_id
            )
            self.log_debug(f"Creating a run for the thread: {thread.id}")

            # Polling for run completion
            while True:
                run_status = self.client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
                self.log_debug(f"Run status: {run_status.status}")
                if run_status.status == "completed":
                    break
                elif run_status.status == "failed":
                    raise Exception("Run failed")
                time.sleep(1)  # Wait before checking again
            self.log_debug(f"Polling for run completion: {run.id}")

            # Fetching all messages from the thread after completion
            messages = self.client.beta.threads.messages.list(thread_id=thread.id)
            self.log_debug(f"Fetching all messages from the thread after completion: {thread.id}")

            # Extracting the assistant's latest response
            assistant_messages = [msg for msg in messages.data if msg.role == 'assistant']
            if not assistant_messages:
                raise Exception("No response from assistant")

            latest_message = assistant_messages[-1]
            response_content_blocks = latest_message.content

            # Collecting text and annotations from content blocks
            response_data = [
                {
                    "text": block.text.value,
                    "annotations": block.text.annotations
                }
                for block in response_content_blocks if block.type == 'text'
            ]

            self.log_debug(f"Assistant's response text and annotations: {response_data}")

            return method_response_template(
                message="Successfully asked assistant",
                data={"response": response_data},
                success=True
            )
        except Exception as e:
            self.log_debug(f"Error asking assistant with ID {assistant_id}: {str(e)}")
            return method_response_template(
                message=f"Failed to ask assistant: {str(e)}",
                data={"assistant_id": assistant_id, "message": message},
                success=False
            )

    # def ask_assistant_with_files(self, assistant_id: str, message: str, file_paths: List[str] = None) -> Dict[str, Any]:
        try:
            # Step 1: Create a Thread
            thread = self.client.beta.threads.create()
            self.log_debug(f"Creating a thread for assistant with ID: {assistant_id}")

            # Step 2: Upload Files and Get their IDs
            attachments = []
            if file_paths:
                for file_path in file_paths:
                    purpose = "vision" if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')) else "assistants"
                    file_id = self.upload_file(file_path, purpose)
                    attachments.append({"file_id": file_id})

            # Step 3: Add a Message with Attachments to the Thread
            self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=message,
                attachments=attachments
            )
            self.log_debug(f"Adding a message with attachments to the thread: {thread.id}")

            # Step 4: Run the Assistant on the Thread
            run = self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=assistant_id
            )
            self.log_debug(f"Creating a run for the thread: {thread.id}")

            # Polling for run completion
            while True:
                run_status = self.client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
                if run_status.status == "completed":
                    break
                elif run_status.status == "failed":
                    raise Exception("Run failed")
                time.sleep(1)  # Wait before checking again
            self.log_debug(f"Polling for run completion: {run.id}")

            # Fetching all messages from the thread after completion
            messages = self.client.beta.threads.messages.list(thread_id=thread.id)
            self.log_debug(f"Fetching all messages from the thread after completion: {thread.id}")

            # Extracting the assistant's latest response
            assistant_messages = [msg for msg in messages.data if msg.role == 'assistant']
            if not assistant_messages:
                raise Exception("No response from assistant")

            latest_message = assistant_messages[-1]
            response_content_blocks = latest_message.content

            # Collecting text and annotations from content blocks
            response_data = [
                {
                    "text": block.text.value,
                    "annotations": block.text.annotations
                }
                for block in response_content_blocks
                if block.type == 'text'
            ]

            self.log_debug(f"Assistant's response text and annotations: {response_data}")

            return method_response_template(
                message="Successfully asked assistant",
                data={"response": response_data},
                success=True
            )
        except Exception as e:
            self.log_debug(f"Error asking assistant with ID {assistant_id}: {str(e)}")
            return method_response_template(
                message=f"Failed to ask assistant: {str(e)}",
                data={"assistant_id": assistant_id, "message": message},
                success=False
            )

    