import os
import tempfile
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, File, UploadFile, Depends, BackgroundTasks, Form
from fastapi.responses import JSONResponse, Response, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

from pypdf import PdfReader

from src.connectors.managers import (
    AzureManager
)
from src.store.cache import (
    SimpleCache, CacheData, background_clear_cache
)


azure_manager = AzureManager();
PDF_CACHE = SimpleCache()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], #origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/hello")
def hello():
    return {"message": "Hello from the NEW WIPJAR backend!"}

@app.post("/extract_text", response_class=JSONResponse)
async def extract_text(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    print(file)
    try:
        if ".txt" in file.filename:
            suffix=".txt"
        else :
            suffix = ".pdf"        # Create a temporary file to save the uploaded PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        if suffix == ".txt":
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
        data = azure_manager.get_file_summary(text)
        data["key"] = file.filename
        PDF_CACHE.set(file.filename, data, 60 * 60 * 24)
        print("Setting cache for: ", file.filename)
        background_tasks.add_task(background_clear_cache, PDF_CACHE)
        response = {
            "usage": data["usage"],
            "key": data["key"],
            "response": data["response"]
        }
        print(data["key"])
        return response
    except Exception as e:
        print(e)
        return PlainTextResponse(content=f"An error occurred: {str(e)}", status_code=500)
    

@app.get("/wipplaces")
def get_places():
    places = azure_manager.get_places()
    if places is not None:
        return {"success": True, "places": places}
    else :
        return {"success": False}