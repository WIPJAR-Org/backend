import os
from src.connectors.clients import gpt4omini_client, blobstorage_client
from uuid import uuid4
import tempfile
import json
from pypdf import PdfReader

class AzureManager:
    def __init__(self) -> None:
        self.chat_client = gpt4omini_client
        self.blobstorage_client = blobstorage_client

    def get_file_summary(self, text: str):
        return self.chat_client.get_pdf_data(text)
    
    def get_full_index(self):
        return self.blobstorage_client.get_full_index()
    
    def get_places(self):
        try:
            placesMetaStr = self.blobstorage_client.get_blob_content('wipjar-pdfs', 'metadata.json')
            if placesMetaStr is None:
                raise IOError ("Error reading blob")
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
    
    def read_txt_pdf_blob(self, blob_name, container_name = 'wipjar-pdfs'):
        suffix = blob_name.split('.')[1]
        print('-->', suffix)
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            content = self.blobstorage_client.get_blob_content(container_name, blob_name)
            temp_file.write(content)
            temp_file_path = temp_file.name
        if suffix == "txt":
            text = content.decode('utf-8')
        else : 
            reader = PdfReader(temp_file_path)
            # reader = None
            number_of_pages = len(reader.pages)
            content = []
            print(number_of_pages)
            for page in reader.pages:
                pgcontent = page.extract_text()
                content.append(pgcontent)
            text = '\n'.join(content)
            # Extract text from the PDF using textract
            # text = textract.process(temp_file_path, method='pdfminer').decode('utf-8')
            os.unlink(temp_file_path)

        # Remove the temporary file
        text = text.replace('\n\n\n', '\n')
        text = text.replace('\n\n', '\n')
        text = text.replace('\n \n', '\n')  

        return text

    async def write_pdf_as_index(self, place, department, date, task_statuses):
        try:
            task_id = f'{place}-{department}-{date}'
            task_statuses[task_id] = "Task is pending..."
            blobs = self.blobstorage_client.read_directories('wipjar-pdfs', starts_with=f'{place}/{department}/{date}')  
            text = ''
            tokens = 0
            messages = ''
            for blob_name in blobs:
                date_time = blob_name.split('/')[2]
                try:
                    text += f'{date_time} \n' + self.read_txt_pdf_blob(blob_name) 
                    num_tokens = self.chat_client.num_tokens_content(text) 
                    print(num_tokens)
                    tokens += num_tokens
                except IOError as e:
                    error_message += f'Failed reading the file {blob_name}: {str(e)}'
                    messages += error_message    
                    print(messages)
            self.blobstorage_client.save_minutes_index('wipjar-minutes-index', f'{place}/{department}/{date}_{tokens}.txt', text)
            print(f'Saved minutes index for {place}/{department}/{date}')
            task_statuses[task_id] = f"File has been written. {messages}"
            return {"text": text, "tokens": tokens}
        except Exception as e:
            task_statuses[task_id] = {"failed": True, "message": str(e)} 
            return {"failed": True, "message": str(e)}

    # revisit this method and add starts_with parameter
    def get_departments(self):
        return self.blobstorage_client.read_directories('wipjar-pdfs')


    def get_directories(self, starts_with, container_name = 'wipjar-pdfs'):
        return self.blobstorage_client.read_directories(container_name, starts_with)

    def get_answer_from_pdf(self, text: str, question: str, json_response: bool):
        return self.chat_client.converse(text, question, json_response)