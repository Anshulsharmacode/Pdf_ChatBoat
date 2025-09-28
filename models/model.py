from pydantic import BaseModel
from datetime import datetime

class User(BaseModel):
   
    userName:str
    email : str
    password: str


class Message (BaseModel):
    id: str 
    user_id: str
    pdf_id : str
    text :str
    created_at :datetime = datetime.utcnow

class Pdf (BaseModel):
    id: str
    filename: str
    filePath: str
    user_id: str
    uploaded_at: datetime = datetime.utcnow