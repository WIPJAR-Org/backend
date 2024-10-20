import os
import tempfile
from uuid import uuid4
import asyncio
import aiofiles
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

app = FastAPI()

azure_manager = AzureManager()
PDF_CACHE = SimpleCache()
CONVERSATION_CACHE = {}
ENCOUNTER_SUMMARY_CACHE = {}
INDEX_CACHE = {}

def get_index_cache():
    return INDEX_CACHE

@app.on_event("startup")
async def startup():
    print("Startup Activities")
    '''
    Load index
    '''
    global INDEX_CACHE 
    INDEX_CACHE = azure_manager.get_full_index()


def get_conversation_cache():
    return CONVERSATION_CACHE

def get_encounter_summary_cache():
    return ENCOUNTER_SUMMARY_CACHE


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

@app.post("/wipindex")
async def create_index(place:str = Form(...), department:str = Form(...), date:str = Form(...)):
    response = await azure_manager.write_pdf_as_index(place, department, date, {})
    return response

@app.post("/wipindex/all")
async def create_index(place_name:str = Form(...)):
    places = azure_manager.get_places()
    departments = []
    task_statuses = {}

    for place in places:
        if place["name"] == place_name:
            departments = place["info"]["departments"]
            break
    
    tasks = []

    for department in departments:
        dept = department["name"]
        blobs = azure_manager.get_directories(starts_with=f'{place_name}/{dept}')
        for blob_name in blobs:
            if '.json' in blob_name:
                continue
            filename = blob_name.split('/')[2]
            datestr = filename.split('_')[0]

            tasks.append(azure_manager.write_pdf_as_index(place_name, dept, datestr, task_statuses))
            # Start the task in a new thread
            # thread = threading.Thread(target=azure_manager.write_pdf_as_index, args=(place_name, dept, datestr, task_statuses))
            # thread.start()
    await asyncio.gather(*tasks)

    return task_statuses


@app.get("/cache")
async def get_cache(background_tasks: BackgroundTasks, key:str = Form(...)):
    value = PDF_CACHE.get(key)
    background_tasks.add_task(background_clear_cache, PDF_CACHE)
    return {"key": key, "value": value}

@app.post("/cache/{key}")
async def set_cache(key: str, data: CacheData, background_tasks: BackgroundTasks):
    PDF_CACHE.set(key, data.value, data.ttl_seconds)
    background_tasks.add_task(background_clear_cache, PDF_CACHE)
    return {"message": "Cache set successfully"}


def load_file_task(batch_id: str, blob_batch):
    # Simulate a long-running task
    data = {}
    data["key"] = batch_id
    data["status"] = "LOADING"
    PDF_CACHE.set(batch_id, data, 60 * 60 * 24) 
    text = ''
    for blob in blob_batch:
        print(blob)
        try:
            text += azure_manager.read_txt_pdf_blob(blob, 'wipjar-minutes-index')
        except Exception as e:
            print(e, blob)
        text += '\n'
    data["text"] = text
    data["status"] = "LOADED"
    PDF_CACHE.set(batch_id, data, 60 * 60 * 24) 

def load_files_in_background(background_tasks: BackgroundTasks, blob_batches):
    batch_ids = []
    for blob_batch in blob_batches:
        batch_id = str(uuid4()) 
        background_tasks.add_task(load_file_task, batch_id, blob_batch)
        batch_ids.append(batch_id)
    return batch_ids

task_statuses = {}

async def write_file_task(task_id: str, filename: str, content: str):
    try:
        # Simulate a long-running task
        await asyncio.sleep(10)
        # Write the file
        async with aiofiles.open(filename, 'w') as f:
            await f.write(content)
        # Update task status
        task_statuses[task_id] = f"File {filename} has been written."
    except Exception as e:
        task_statuses[task_id] = f"Error: {str(e)}"

@app.post("/schedule-task")
async def schedule_task(filename: str, content: str):
    task_id = str(uuid4())
    task_statuses[task_id] = "Task is pending..."
    
    # Start the task in a new thread
    asyncio.create_task(write_file_task(task_id, filename, content))
    
    return {"message": "Task scheduled successfully", "task_id": task_id}

@app.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    status = task_statuses.get(task_id, "Task not found")
    return {"task_id": task_id, "status": status}

@app.get("/tasks")
async def get_tasks():
    return task_statuses