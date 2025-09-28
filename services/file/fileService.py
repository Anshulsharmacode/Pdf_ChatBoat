from datetime import datetime
import os
import shutil
from fastapi import UploadFile
# from conf.db import pdf_collection
from constant.extra import extract_text_from_pdf, save_pdf, save_user
from models.model import User
from conf.db import pdf_collection


UPLOAD_FOLDER = "uploads"  
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def upload_file(file : UploadFile , user_id):
    if not file :
        return {"error": "not found file"}
    
    file_path = os.path.join(UPLOAD_FOLDER , file.filename)
    print(file_path)

    with open (file_path , "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    pdf = {
    "filename": file.filename,
    "filePath": file_path,
    "user_id": user_id,
    "uploaded_at": datetime.utcnow()
    }
    save_pdf(pdf)


    return {
        'file Name': file.filename,
        'saved path': file_path
    }


def getFileText(user_id):
    print(user_id)

    pdf= pdf_collection.find_one({"user_id":user_id})
    print(pdf)
    if not pdf :
        return {"error": "not found"}
    
    file_path = pdf['filePath']

    text = extract_text_from_pdf(file_path)
    return text
    
