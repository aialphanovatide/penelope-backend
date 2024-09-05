"""
# Vector store module: create, update, delete, list, get vector store details, it is used to store the documents in a vector database.
"""

from app.utils.response_template import method_response_template
from typing import List, Dict, Any, Optional, Literal
from werkzeug.datastructures import FileStorage
from openai import OpenAI
import contextlib
import logging
import os

class VectorStoreManager:
    def __init__(self, api_key: Optional[str] = None, verbose: bool = False):

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided and OPENAI_API_KEY environment variable not set") 
        
        self.verbose = verbose
        self.client = OpenAI(api_key=self.api_key)
        self.logger = logging.getLogger(__name__)
        self.extensions = ['.pdf', '.txt']

        if self.verbose:
            logging.basicConfig(level=logging.DEBUG)

    def log_debug(self, message: str, *args, **kwargs):
        if self.verbose:
            self.logger.debug(message, *args, **kwargs)

    def create_vector_store(self, name: str, 
                            file_ids: Optional[List[str]] = None,
                            ) -> Dict[str, Any]:
        """
        Create a new vector store with the specified parameters.

        Args:
            name (str): The name of the vector store.
            file_ids (Optional[List[str]]): A list of file IDs to associate with the vector store. Defaults to Non

        Returns:
            Dict[str, Any]: A dictionary containing the details of the created vector store.

        Raises:
            Exception: If there's an error during vector store creation.
        """
        try:
            vector_store = self.client.beta.vector_stores.create(
                name=name,
                file_ids=file_ids or [],
            )
            self.log_debug(f"Vector store created successfully: {vector_store.id}")
            return method_response_template(message="Vector store created successfully", 
                                             data=vector_store.model_dump(), 
                                             success=True
                                             )
        except Exception as e:
            error_message = f"Error creating vector store: {str(e)}"
            self.log_debug(error_message)
            return method_response_template(message=error_message, 
                                             data=None, 
                                             success=False
                                             )

    def list_vector_stores(self, limit: int = 20, order: str = "desc", 
                           after: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all vector stores, up to the specified limit.

        Args:
            limit (int): The maximum number of vector stores to return. Default is 20.
            order (str): The order of the vector stores. Can be "asc" or "desc". Default is "desc".
            after (Optional[str]): A cursor for use in pagination. `after` is an object ID that defines your place in the list. Default is None.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each containing the details of a vector store.

        Raises:
            VectorStoreError: If there's an error during the listing process.
        """
        try:
            vector_stores = self.client.beta.vector_stores.list(
                limit=limit,
                order=order,
                after=after
            )
            self.log_debug(f"Successfully retrieved {len(vector_stores.data)} vector stores")
            return method_response_template(message=f"Successfully retrieved {len(vector_stores.data)} vector stores", 
                                             data=[vs.model_dump() for vs in vector_stores.data], 
                                             success=True
                                             )
        except Exception as e:
            error_message = f"Error listing vector stores: {str(e)}"
            self.logger.error(error_message)
            return method_response_template(message=error_message, 
                                             data=None, 
                                             success=False
                                             )

    def delete_vector_store(self, vector_store_id: str) -> Dict[str, Any]:
        """
        Delete a vector store by its ID.

        Args:
            vector_store_id (str): The ID of the vector store to delete.

        Returns:
            Dict[str, Any]: A dictionary containing the response message, deleted vector store data (if successful),
                            and a success flag.

        Raises:
            Exception: If there's an error during the deletion process.
        """
        try:
            self.log_debug(f"Attempting to delete vector store with ID: {vector_store_id}")
            deleted_vector_store = self.client.beta.vector_stores.delete(vector_store_id)
            self.log_debug(f"Successfully deleted vector store with ID: {vector_store_id}")
            return method_response_template(
                message="Vector store deleted successfully",
                data=deleted_vector_store.model_dump(),
                success=True
            )
        except Exception as e:
            error_message = f"Error deleting vector store with ID {vector_store_id}: {str(e)}"
            self.log_debug(error_message)
            return method_response_template(
                message=error_message,
                data={"vector_store_id": vector_store_id},
                success=False
            )

    def update_vector_store_name(self, vector_store_id: str, name: Optional[str] = None, 
                            ) -> Dict[str, Any]:
        """
        Update a vector store with the provided parameters.

        Args:
            vector_store_id (str): The ID of the vector store to update.
            name (Optional[str]): The new name for the vector store. If None, the name remains unchanged.
            description (Optional[str]): The new description for the vector store. If None, the description remains unchanged.

        Returns:
            Dict[str, Any]: A dictionary containing the response message, updated vector store data, and a success flag.

        Raises:
            Exception: If there's an error during the update process.
        """
        try:
            self.log_debug(f"Attempting to update vector store with ID: {vector_store_id}")
            updated_vector_store = self.client.beta.vector_stores.update(
                vector_store_id,
                name=name,
            )
            self.log_debug(f"Successfully updated vector store with ID: {vector_store_id}")
            return method_response_template(
                message="Vector store updated successfully",
                data=updated_vector_store.model_dump(),
                success=True
            )
        except Exception as e:
            error_message = f"Error updating vector store with ID {vector_store_id}: {str(e)}"
            self.log_debug(error_message)
            return method_response_template(
                message=error_message,
                data={"vector_store_id": vector_store_id},
                success=False
            )

    def list_vector_store_files(self, vector_store_id: str, 
                                filter: str | Literal['in_progress', 'completed', 'failed', 'cancelled'],
                                limit: int = 20, 
                                order: str = "desc", 
                                after: Optional[str] = None) -> Dict[str, Any]:
        """
        List files in a vector store.

        Args:
            vector_store_id (str): The ID of the vector store to list files from.
            filter (str | Literal['in_progress', 'completed', 'failed', 'cancelled']): Filter files by status.
            limit (int, optional): The maximum number of files to return. Defaults to 20.
            order (str, optional): The order of the files. Can be "asc" or "desc". Defaults to "desc".
            after (Optional[str], optional): A cursor for use in pagination. Defaults to None.

        Returns:
            Dict[str, Any]: A dictionary containing the list of files, success status, and additional metadata.

        Raises:
            ValueError: If an invalid order is provided.
            Exception: If there's an error during the API call.
        """
        try:
            if order not in ["asc", "desc"]:
                raise ValueError("Invalid order. Must be 'asc' or 'desc'.")

            files = self.client.beta.vector_stores.files.list(
                vector_store_id=vector_store_id,
                limit=limit,
                order=order,
                after=after,
                filter=filter
            )
            file_list = [file.model_dump() for file in files.data]

            self.log_debug(f"Successfully retrieved {len(file_list)} files from vector store {vector_store_id}.")
            return method_response_template(
                message="Successfully retrieved vector store files",
                data={
                    "files": file_list,
                    "total_files": len(file_list),
                    "has_more": files.has_more,
                    "next_cursor": files.next_cursor
                },
                success=True
            )
        except Exception as e:
            self.log_debug(f"Error listing vector store files: {str(e)}")
            return method_response_template(
                message=f"Failed to list vector store files: {str(e)}",
                data={"vector_store_id": vector_store_id, "limit": limit, "order": order, "after": after, "filter": filter},
                success=False
            )
    
    def get_file_paths(self, root_folder: str, extensions: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Recursively lists absolute paths to documents (files) within a root folder, filtered by extensions.

        Args:
            root_folder (str): The root folder to start the search from.
            extensions (Optional[List[str]]): List of file extensions to filter. Example: ['.pdf', '.txt'].
                                              If None, uses self.extensions.

        Returns:
            Dict[str, Any]: A dictionary containing:
                - 'success' (bool): True if the operation was successful, False otherwise.
                - 'message' (str): A descriptive message about the operation result.
                - 'data' (Dict[str, Any]): A dictionary containing:
                    - 'file_paths' (List[str]): List of absolute paths to documents found matching the extensions.
                    - 'total_files' (int): Total number of files found.
                    - 'extensions_used' (List[str]): The extensions used for filtering.

        Raises:
            FileNotFoundError: If the root_folder does not exist.
            PermissionError: If there's no permission to access the root_folder or its subdirectories.
        """
        try:
            if not os.path.exists(root_folder):
                raise FileNotFoundError(f"The specified root folder '{root_folder}' does not exist.")

            file_paths = []
            extensions_used = extensions if extensions is not None else self.extensions

            for root, _, files in os.walk(root_folder):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    _, file_ext = os.path.splitext(file_name)
                    if file_ext.lower() in extensions_used:
                        file_paths.append(file_path)

            return method_response_template(
                message="Successfully listed documents",
                data={
                    "file_paths": file_paths,
                    "total_files": len(file_paths),
                    "extensions_used": extensions_used
                },
                success=True
            )

        except PermissionError as pe:
            self.log_debug(f"Permission error: {str(pe)}")
            return method_response_template(
                message=f"Permission error: {str(pe)}",
                data={"root_folder": root_folder},
                success=False
            )
        except Exception as e:
            self.log_debug(f"Error listing documents in {root_folder}: {str(e)}")
            return method_response_template(
                message=f"Error listing documents: {str(e)}",
                data={"root_folder": root_folder},
                success=False
            )
    
    def add_local_files_to_vector_store(
        self,
        vector_store_id: str,
        file_paths: List[str],
        batch_size: int = 200,
    ) -> Dict[str, Any]:
        """
        Add files to a vector store in batches.

        This method uploads files to the specified vector store in batches, allowing for
        efficient processing of large numbers of files.

        Args:
            vector_store_id (str): The ID of the vector store to update.
            file_paths (List[str]): A list of local file paths to add to the vector store.
            batch_size (int, optional): The number of files to process in each batch. Defaults to 200.
            name (Optional[str], optional): New name for the vector store. Defaults to None.
            description (Optional[str], optional): New description for the vector store. Defaults to None.

        Returns:
            Dict[str, Any]: A dictionary containing the update status and details, including:
                - total_files_added (int): The total number of files successfully added.
                - batch_results (List[Dict]): Results for each batch, including batch number,
                  status, and file counts.

        Raises:
            Exception: If there's an error updating the vector store or processing batches.

        Note:
            This method uses the OpenAI API's beta vector stores functionality.
        """
        try:
            total_files_added = 0
            batch_results = []

            for i in range(0, len(file_paths), batch_size):
                batch_paths = file_paths[i:i + batch_size]
                with self._open_file_streams(batch_paths) as file_streams:
                    if file_streams:
                        batch_result = self._process_local_files_batch(vector_store_id, file_streams, i, batch_size)
                        batch_results.append(batch_result)
                        total_files_added += batch_result['file_counts'].completed
                    else:
                        self.log_debug(f"Batch {i // batch_size + 1}: No valid files to upload.")

            return {
                "total_files_added": total_files_added,
                "batch_results": batch_results
            }

        except Exception as e:
            error_message = f"Error updating vector store: {str(e)}"
            self.log_debug(error_message)
            return method_response_template(
                message=error_message,
                data={"vector_store_id": vector_store_id, "file_paths": file_paths, "batch_size": batch_size},
                success=False
            )

    def _process_local_files_batch(self, vector_store_id: str, file_streams, 
                            start_index: int, batch_size: int) -> Dict[str, Any]:
        """Process a batch of files and return the result."""
        try:
            file_batch = self.client.beta.vector_stores.file_batches.upload_and_poll(
                vector_store_id=vector_store_id,
                files=file_streams
            )
            return {
                "batch_number": start_index // batch_size + 1,
                "status": file_batch.status,
                "file_counts": file_batch.file_counts
            }
        except Exception as e:
            self.log_debug(f"Error in batch {start_index // batch_size + 1}: {str(e)}")
            return {
                "batch_number": start_index // batch_size + 1,
                "error": str(e)
            }

    def add_files_to_vector_store(
        self,
        vector_store_id: str,
        files: List[FileStorage],
        batch_size: int = 200,
    ) -> Dict[str, Any]:
        try:
            total_files_added = 0
            batch_results = []

            for i in range(0, len(files), batch_size):
                batch_files = files[i:i + batch_size]
                batch_result = self._process_file_batch(vector_store_id, batch_files, i, batch_size)
                batch_results.append(batch_result)
                total_files_added += batch_result['file_counts'].completed

            return {
                "total_files_added": total_files_added,
                "batch_results": batch_results
            }

        except Exception as e:
            error_message = f"Error updating vector store: {str(e)}"
            self.log_debug(error_message)
            return method_response_template(
                message=error_message,
                data={"vector_store_id": vector_store_id, "file_count": len(files), "batch_size": batch_size},
                success=False
            )

    def _process_file_batch(self, vector_store_id: str, files: List[FileStorage], 
                        start_index: int, batch_size: int) -> Dict[str, Any]:
        try:
            file_batch = self.client.beta.vector_stores.file_batches.upload_and_poll(
                vector_store_id=vector_store_id,
                files=files
            )
            return {
                "batch_number": start_index // batch_size + 1,
                "status": file_batch.status,
                "file_counts": file_batch.file_counts
            }
        except Exception as e:
            self.log_debug(f"Error in batch {start_index // batch_size + 1}: {str(e)}")
            return {
                "batch_number": start_index // batch_size + 1,
                "error": str(e)
            }
    
    @contextlib.contextmanager
    def _open_file_streams(self, paths: List[str]):
        """Context manager to safely open and close file streams."""
        file_streams = []
        try:
            for path in paths:
                if os.path.exists(path):
                    file_streams.append(open(path, "rb"))
                else:
                    self.log_debug(f"File not found: {path}")
            yield file_streams
        finally:
            for file in file_streams:
                file.close()


