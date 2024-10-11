from src.connectors.clients import gpt4omini_client 
from uuid import uuid4

class AzureManager:
    def __init__(self) -> None:
        self.chat_client = gpt4omini_client 

    def get_file_summary(self, text: str):
        return self.chat_client.get_pdf_data(text)