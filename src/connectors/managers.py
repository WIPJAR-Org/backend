from src.connectors.clients import gpt4omini_client, blobstorage_client
from uuid import uuid4
import json

class AzureManager:
    def __init__(self) -> None:
        self.chat_client = gpt4omini_client 
        self.blobstorage_client = blobstorage_client

    def get_file_summary(self, text: str):
        return self.chat_client.get_pdf_data(text)
    
    def get_places(self):
        try:
            placesMetaStr = self.blobstorage_client.get_blob_content('wipjar-pdfs', 'metadata.json')
            if placesMetaStr is None:
                raise Exception("Error reading blob")
            placesMeta = json.loads(placesMetaStr)
            places = placesMeta["places"]
            places_data = []
            for place in places :
                place_meta_str = self.blobstorage_client.get_blob_content('wipjar-pdfs', f'{place}/metadata.json')
                place_meta = json.loads(place_meta_str)
                places_data.append({
                    "name": place,
                    "info": place_meta 
                })
            return places_data
        except Exception as e:
            print("Error parsing blob ", e)