from datetime import datetime
import os
import shutil
from fastapi import HTTPException, UploadFile
# from conf.db import pdf_collection
from constant.extra import extract_text_from_pdf, save_pdf, save_user
from models.model import User
from conf.db import pdf_collection , message_collection


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
    
def get_File_histroy(user_id):
    try:
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
        
       
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$sort": {"created_at": -1}},
            {
                "$group": {
                    "_id": "$pdf_id",
                    "messages": {
                        "$push": {
                            "question": "$question",
                            "answer": "$answer",
                            "created_at": "$created_at"
                        }
                    },
                    "last_message": {"$first": "$created_at"}
                }
            },
            {
                "$lookup": {
                    "from": "pdfs",
                    "localField": "_id",
                    "foreignField": "_id",
                    "as": "pdf_info"
                }
            },
            {
                "$match": {
                    "pdf_info": {"$ne": []}  
                }
            },
            {"$unwind": "$pdf_info"},
            {
                "$project": {
                    "filename": "$pdf_info.filename",
                    "messages": 1,
                    "last_message": 1
                }
            },
            {"$sort": {"last_message": -1}}
        ]
        
        sessions = list(message_collection.aggregate(pipeline))
        
        # Handle empty results
        if not sessions:
            return {"sessions": []}
        
        # Convert ObjectId and datetime to strings for JSON serialization
        for session in sessions:
            session["_id"] = str(session["_id"])
            session["last_message"] = session["last_message"].isoformat()
            for msg in session["messages"]:
                msg["created_at"] = msg["created_at"].isoformat()
        
        return {"sessions": sessions}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching chat history: {str(e)}")