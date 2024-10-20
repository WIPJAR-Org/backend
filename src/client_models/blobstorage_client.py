"""
This module handles interactions with Azure Blob Storage.
"""
import base64
import json
import random
import string
from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob import BlobServiceClient, BlobClient

from typing import TypedDict

class BlobStorageClient:
    """
    Manages interactions with Azure Blob Storage.
    """
    def __init__(self, access_key: str) -> None:
        """
        Initialize the BlobStorageClient with the necessary connection string.

        Args:
            connection_string (str): The connection string for Azure Blob Storage.
        """
        self.blobstorage_client = BlobServiceClient.from_connection_string(f"DefaultEndpointsProtocol=https;AccountName=filestoragewipjarai;AccountKey={access_key};EndpointSuffix=core.windows.net")


    def read_file(self, container_name, blob_name):
        """
        Download a blob from Azure Blob Storage to a local file.

        Args:
            container_name (str): The name of the container.
            blob_name (str): The name of the blob.
            file_path (str): The local file path to save the blob.

        Returns:
            Optional[str]: The file path if successful, None otherwise.
        """
        blob_client = self.blobstorage_client.get_blob_client(container=container_name, blob=blob_name)
        if blob_client.exists():
            download_stream = blob_client.download_blob()
            content = download_stream.readall()
            text_content = content.decode('utf-8')
            return text_content
        else:
            return False

    def get_full_index(self):
        '''
        Best case scenario: test-index container has all files with test-aliases
        with up-to-date statuses
        '''
        index_content = self.read_all_files("test-index")
        return index_content
    
    def create_container_if_not_exists(self, container_name):
        """
        Create the container if it does not exist.

        Args:
            container_name (str): The name of the container.
        """
        container_client = self.blobstorage_client.get_container_client(container_name)
        try:
            container_client.create_container()
        except ResourceNotFoundError:
            pass # Container already exists

    def read_all_files(self, container_name, index_content={}):
        try:
            self.create_container_if_not_exists(container_name)
            container_client = self.blobstorage_client.get_container_client(container_name)
            blob_list = container_client.list_blob_names()
            for blob_name in blob_list:
                filecontent = self.read_file(container_name, blob_name)
                if not filecontent:
                    continue
                try:
                    test_data = json.loads(filecontent)
                    index_content[test_data["test_alias"]] = {
                        "test_name": test_data["test_name"],
                        "test_alias": test_data["test_alias"],
                        "status": test_data["status"]
                    }
                except json.JSONDecodeError as e:
                    print.error(f"Error parsing file content: {blob_name}, {e}")
                    print.debug(filecontent)
        except ResourceNotFoundError as e:
            print.error(f"Container '{container_name}' not found: {e}")
        except Exception as e:
            print.error(f"An unexpected error occurred: {e}")
        return index_content

    def read_directories(self, container_name, starts_with):
        """
        List directories in a container that start with a given prefix.

        Args:
            container_name (str): The name of the container.
            starts_with (str): The prefix to filter directories.

        Returns:
            list: A list of directory names.
        """
        container_client = self.blobstorage_client.get_container_client(container=container_name)
        blob_list = container_client.list_blob_names(name_starts_with=starts_with)
        blob_names = []
        for blob in blob_list:
            blob_names.append(blob)
            print("\t" + blob)
        return blob_names

    def save_minutes_index(self, container_name, blob_name, content):
        blob_client = self.blobstorage_client.get_blob_client(container=container_name, blob=blob_name)
        blob_client.upload_blob(json.dumps(content), overwrite=True)

    def get_blob_content(self, container_name, blob_name):
        """
        Get the content of a blob in a container.

        Args:
            container_name (str): The name of the container.
            blob_name (str): The name of the blob.     
        
        Returns:
            bytes: The content of the blob. 
        """        
        container_client = self.blobstorage_client.get_container_client(container=container_name)
        try :
            return container_client.download_blob(blob_name).readall()
        except ResourceNotFoundError:
            print(f'File {blob_name} not found in container {container_name}')
            return None 