import base64
import json
import random

from azure.storage.blob import BlobServiceClient, BlobClient

from typing import TypedDict

class BlobStorageClient:
    def __init__(self, access_key: str) -> None:
        self.blobstorage_client = BlobServiceClient.from_connection_string(f"DefaultEndpointsProtocol=https;AccountName=filestoragewipjarai;AccountKey={access_key};EndpointSuffix=core.windows.net")


    def read_file(self, container_name, blob_name):
        blob_client = self.blobstorage_client.get_blob_client(container=container_name, blob=blob_name)
        if blob_client.exists() :
            download_stream = blob_client.download_blob()
            content = download_stream.readall()
            text_content = content.decode('utf-8')
            return text_content
        else:
            return False

    def read_directories(self, container_name, starts_with):
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
        container_client = self.blobstorage_client.get_container_client(container=container_name)
        try :
            return container_client.download_blob(blob_name).readall()
        except :
            print('File not found')
            return None 