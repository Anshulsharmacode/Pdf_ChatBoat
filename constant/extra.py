
from models.model import User
from pypdf import PdfReader 
from passlib.context import CryptContext
from conf.db import user_collection ,pdf_collection

def extract_text_from_pdf(file_path):
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text


pwd = CryptContext(schemes=['bcrypt'], deprecated='auto')

def hashPassword(password:str):
    return pwd.hash(password)

def verify_password(password:str , has_Password:str):
    return pwd.verify(password ,has_Password)

# def save_user (user:User):
#     return user_collection.insert_one(user.dict())
    

def get_user_by_email(email: str) -> User | None:
    data = user_collection.find_one({"email": email})
    data["_id"] = str(data['_id'])
    return data

def save_user(user: dict):
    result = user_collection.insert_one(user)
    saved_user = user_collection.find_one({"_id": result.inserted_id})
    # Convert ObjectId to str for JSON
    saved_user["_id"] = str(saved_user["_id"])
    return saved_user


def save_pdf(user: dict):
    result = pdf_collection.insert_one(user)
    saved_user = pdf_collection.find_one({"_id": result.inserted_id})
    # Convert ObjectId to str for JSON
    saved_user["_id"] = str(saved_user["_id"])
    return saved_user