import os
from src.client_models.gpt4o_client import GPT4OClient
from src.client_models.blobstorage_client import BlobStorageClient

gpt4omini_client = GPT4OClient(
    api_base=os.getenv("WJ_OPENAI_API_BASE"),
    api_key=os.getenv("WJ_OPENAI_API_KEY"),
    api_version=os.getenv("GPT4oMiniV_API_VERSION"),
    deployment_name=os.getenv("WJ_DEPLOYMENT_NAME_4omini"),
)

blobstorage_client = BlobStorageClient(
    access_key=os.getenv("WJ_BLOB_ACCESS_KEY")
);