from fastapi import FastAPI, Depends, File, Form, HTTPException, UploadFile
from datetime import datetime
from bson import ObjectId

from jwt_Str.access import verify_token
from services.llm.llm import injestPdf, takeLLMresponse
from services.file.fileService import get_File_histroy, getFileText, upload_file
from services.user.dto import ChatRequest, LoginResponseDTO, UserSignupDTO, UserLoginDTO, UserResponseDTO
from services.user.user_service import User_Service
from fastapi.middleware.cors import CORSMiddleware
from conf.db import message_collection  # Add this import

app = FastAPI(title="chat_pdf", version ="0.1")

origins = [
    "http://localhost:5173",  
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

user_service = User_Service()

@app.post('/signup')
def signup(signup_data: UserSignupDTO):
    return user_service.signUp(signup_data)


# @app.post('/signup', response_model=UserResponseDTO)
# def signup(signup_data: UserSignupDTO):
#     return user_service.signUp(signup_data)

@app.post('/login', response_model=LoginResponseDTO)
def login(login: UserLoginDTO):
    return user_service.login(login)


@app.get("/me")
def validToken(current_user:dict= Depends(verify_token)):
    print("current user",current_user)

@app.post("/upload")
def upload(file: UploadFile = File(...),current_user:dict= Depends(verify_token)):
    return upload_file(file, current_user["user_id"])

@app.post("/inset")
def chat(current_user:dict= Depends(verify_token)):
    return injestPdf(current_user['user_id'])

@app.post("/llm")
def chat(data:ChatRequest , current_user:dict= Depends(verify_token)):
    return takeLLMresponse(current_user['user_id'],data.user_question)

@app.get("/chat-history")
def get_chat_history(current_user: dict = Depends(verify_token)):
    return get_File_histroy(current_user['user_id'])