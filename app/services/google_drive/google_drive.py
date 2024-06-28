import os
import io
import json
from typing import List, Dict, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseDownload
from google_auth_oauthlib.flow import InstalledAppFlow

class GoogleDrive:
    """
    A class to interact with Google Drive API and manage files and folders.

    Attributes:
        credentials_file (str): Path to the credentials JSON file for OAuth authentication.
        folder_names (List[str]): List of folder names to work with in Google Drive.
        service (object): Google Drive API service object.
        local_paths (List[str]): List of local paths where downloaded files are saved.
        root_folder (Optional[str]): Name of the root folder where files were downloaded.
    """

    def __init__(self, credentials_file: str):
        """
        Initializes the GoogleDrive instance with provided credentials and folder names.

        Args:
            credentials_file (str): Path to the credentials JSON file.
            folder_names (List[str]): List of folder names in Google Drive to work with.

        Raises:
            ValueError: If `credentials_file` is not provided.
            RuntimeError: If failed to initialize Google Drive service.
        """
        if not credentials_file:
            raise ValueError('Credential file required')
        
        self.credentials_file = credentials_file
        self.local_paths = []
        self.local_root_folder = 'penelope_database'
        self.service = self.init_drive_client()
        if not self.service:
            raise RuntimeError('Failed to initialize Google Drive service')

    def init_drive_client(self) -> Optional[object]:
        """
        Initializes the Google Drive API client by handling the authorization flow and returning the service object.

        Returns:
            object: Google Drive service object or None if an error occurs.
        """
        creds = None
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json")
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, scopes=['https://www.googleapis.com/auth/drive'])
                creds = flow.run_local_server(port=0)
            with open("token.json", "w") as token:
                token.write(creds.to_json())
        
        try:
            service = build("drive", "v3", credentials=creds)
            return service
        except HttpError as error:
            print(f"An error occurred: {error}")
            return None

    def get_folders_and_files(self, folder_names: List[str], save: bool = False) -> Optional[str]:
        """
        Connects to the Google Drive API client, finds all folders matching the specified names (case-insensitive),
        recursively retrieves all files and subfolders inside them with additional metadata,
        and optionally saves the result to a JSON file.

        Args:
            folder_names (List[str]): List of folder names to search for in Google Drive.
            save (bool, optional): Flag indicating whether to save the result to a JSON file. Default is False.

        Returns:
            Optional[str]: If `save=True`, returns the path where the JSON file is saved. Otherwise, returns None.
        """
        folders_and_files = []

        try:
            for folder_name in folder_names:
                folder_results = self.service.files().list(
                    q=f"mimeType='application/vnd.google-apps.folder' and name contains '{folder_name.lower()}'",
                    spaces='drive',
                    fields="files(id, name)"
                ).execute()

                folders = folder_results.get("files", [])

                if not folders:
                    print(f"No folders found with name '{folder_name}'.")
                    continue

                for folder in folders:
                    if folder['name'].lower() != folder_name.lower():
                        continue
                
                    folder_dict = self.get_folder_contents(folder['id'], folder['name'], "")
                    folders_and_files.append(folder_dict)

            print("\nFolder information retrieved.")

            # Save to JSON file (optional)
            if save:
                with open('folders_and_files.json', 'w', encoding='utf-8') as f:
                    json.dump(folders_and_files, f, indent=2, ensure_ascii=False)

            return folders_and_files

        except HttpError as error:
            print(f"An error occurred: {error}")
            return None

    def get_folder_contents(self, folder_id: str, folder_name: str, current_path: str) -> Dict:
        """
        Recursively retrieves contents of a folder from Google Drive and downloads files if needed.

        Args:
            folder_id (str): ID of the folder in Google Drive.
            folder_name (str): Name of the folder.
            current_path (str): Current path of the folder in the local file system.

        Returns:
            Dict: A dictionary containing folder information.
        """
        folder_dict = {
            "folder_name": folder_name,
            "folder_id": folder_id,
            "contents": []
        }
    
        new_path = os.path.join(current_path, folder_name) if current_path else folder_name

        results = self.service.files().list(
            q=f"'{folder_id}' in parents",
            spaces='drive',
            fields="files(id, name, mimeType, fullFileExtension, size, modifiedTime, createdTime, webViewLink)"
        ).execute()

        items = results.get("files", [])

        for item in items:
            item_type = self.get_file_type(item['mimeType'])
            size_mb = self.convert_size_to_mb(item.get('size'))
            file_extension = self.get_file_extension(item['mimeType'])

            file_path = os.path.join(self.transform_string(new_path), f'{self.transform_string(item['name'])}{file_extension}')
            # Concatenate the prefix at the beginning of the file_path
            file_path = os.path.join(self.local_root_folder, file_path)
            
            if size_mb is not None and size_mb > 500:
                print(f"Skipping large file: {item['name']} (Size: {size_mb:.2f} MB)")
                continue

            item_dict = {
                "name": item['name'],
                "id": item['id'],
                "type": item_type,
                "mimeType": item['mimeType'],
                "fileExtension": file_extension,
                "size": f"{size_mb:.2f} MB" if size_mb is not None else 'N/A',
                "modifiedTime": item.get('modifiedTime'),
                "createdTime": item.get('createdTime'),
                "webViewLink": item.get('webViewLink', ''),
                "googleDrivePath": file_path,
            }

            if item_type == 'folder':
                sub_folder_dict = self.get_folder_contents(item['id'], item['name'], new_path)
                item_dict.update(sub_folder_dict)
            else:
                res = self.download_file(item['id'], item['name'], file_path=file_path)
                if not res:
                    continue

            folder_dict["contents"].append(item_dict)

        return folder_dict
    
    def download_file(self, file_id: str, file_name: str, file_path: str) -> bool:
        """
        Downloads a file from Google Drive and saves it locally.

        Args:
            file_id (str): ID of the file in Google Drive.
            file_name (str): Name of the file.
            file_path (str): Local path where the file will be saved.

        Returns:
            bool: True if download and save are successful, False otherwise.
        """
        print(f"\nAttempting to download: {file_name}")

        try:
            # Attempt to get the file media content
            request = self.service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                print(f"--- Download {int(status.progress() * 100)}% complete ---")

            # Create directories if they do not exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Write the file content to the local disk
            with open(file_path, 'wb') as f:
                f.write(fh.getvalue())
            print(f"\n --- File saved: {file_path} ---")

            # Store local path in instance variable
            self.local_paths.append(file_path)

            return True

        except HttpError as error:
            if error.resp.status == 403:
                try:
                    # If direct download fails, try exporting as PDF
                    request = self.service.files().export_media(fileId=file_id, mimeType='application/pdf')
                    print(f" --- Exporting {file_name} as PDF ---")
                    fh = io.BytesIO()
                    downloader = MediaIoBaseDownload(fh, request)
                    done = False
                    while done is False:
                        status, done = downloader.next_chunk()
                        print(f"--- Download {int(status.progress() * 100)}% complete ---")

                    os.makedirs(os.path.dirname(file_path), exist_ok=True)

                    # Write the exported PDF content to the local disk
                    with open(file_path, 'wb') as f:
                        f.write(fh.getvalue())
                    print(f"\n --- File saved: {file_path} ---")

                    # Store local path in instance variable
                    self.local_paths.append(file_path)

                    return True

                except HttpError as export_error:
                    print(f"Failed to export {file_name} as PDF: {export_error}")
                    return False
            else:
                print(f"Error downloading {file_name}: {error}")
                return False

    def convert_size_to_mb(self, size_str: str) -> Optional[float]:
        """
        Converts file size from bytes string to megabytes float.

        Args:
            size_str (str): File size in bytes.

        Returns:
            Optional[float]: File size in megabytes or None if conversion fails.
        """
        try:
            size_bytes = int(size_str)
            return size_bytes / (1024 * 1024)  # Convert bytes to MB
        except (ValueError, TypeError):
            return None

    def get_file_type(self, mime_type: str) -> str:
        """
        Determines file type based on MIME type.

        Args:
            mime_type (str): MIME type of the file.

        Returns:
            str: File type based on MIME type.
        """
        mime_type_to_type = {
            'application/vnd.google-apps.folder': 'folder',
            'application/pdf': 'pdf',
            'image/png': 'image',
            'image/jpeg': 'image',
            'image/gif': 'git',
            'text/plain': 'text',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'sheet',
            'application/vnd.google-apps.document': 'gdoc',
            'application/vnd.google-apps.spreadsheet': 'gsheet',
            'application/vnd.google-apps.presentation': 'gslides',
            'application/vnd.ms-excel': 'sheet',
            'application/msword': 'doc',
            'application/zip': 'archive',
            'application/x-rar-compressed': 'archive',
            'text/csv': 'csv',
            'application/json': 'json',
            'text/html': 'html'
        }

        if 'image/' in mime_type:
            return 'image'
        elif 'text/' in mime_type:
            return 'text'

        return mime_type_to_type.get(mime_type, 'other')
        
    def get_file_extension(self, mime_type: str) -> str:
        """
        Returns the file extension based on the MIME type.

        Args:
            mime_type (str): MIME type of the file.

        Returns:
            str: File extension including the leading dot.
        """
        mime_type_to_extension = {
            'application/pdf': '.pdf',
            'image/png': '.png',
            'text/plain': '.txt',
            'image/jpeg': '.jpg',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
            'application/vnd.ms-excel': '.xls',
            'application/msword': '.doc',
            'application/zip': '.zip',
            'application/x-rar-compressed': '.rar',
            'text/csv': '.csv',
            'application/json': '.json',
            'text/html': '.html',
        }

        return mime_type_to_extension.get(mime_type, '.pdf') 
    
    def transform_string(self, input_string: str) -> str:
        """
        Transforms the input string by:
        1. Removing forbidden characters for Windows and macOS filenames.
        2. Replacing consecutive spaces with a single space.
        3. Replacing remaining spaces with underscores.
        4. Removing consecutive underscores.
        5. Converting the string to lowercase.

        Args:
            input_string (str): The string to be transformed.

        Returns:
            str: The transformed string.

        Raises:
            TypeError: If the input is not a string.
        """
        try:
            if not isinstance(input_string, str):
                raise TypeError("Input must be a string")

            # List of forbidden characters for Windows and macOS filenames
            forbidden_chars = ['\\', ':', '*', '?', '"', '<', '>', '|', '\0', '-', ',']
            
            # Remove forbidden characters
            for char in forbidden_chars:
                input_string = input_string.replace(char, '')
            
            # Replace consecutive spaces with a single space
            input_string = ' '.join(input_string.split())
            
            # Replace spaces with underscores
            input_string = input_string.replace(' ', '_')
            
            # Remove consecutive underscores
            while '__' in input_string:
                input_string = input_string.replace('__', '_')
            
            # Convert to lowercase
            result = input_string.casefold()
            
            return result

        except TypeError as e:
            print(f"Error transforming string: {e}")
            return ""

# # Example usage:
credentials_file_path = 'credentials.json'
folder_names = ['Database']

try:
    google_drive = GoogleDrive(credentials_file_path)

    # Download documents locally
    google_drive.get_folders_and_files(folder_names=folder_names, save=True)
  
except ValueError as ve:
    print(f"ValueError: {ve}")
except RuntimeError as re:
    print(f"RuntimeError: {re}")
