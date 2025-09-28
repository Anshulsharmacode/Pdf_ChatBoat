from pydantic import BaseModel, EmailStr

# Signup request
class UserSignupDTO(BaseModel):
    userName: str
    email: EmailStr
    password: str

# Login request
class UserLoginDTO(BaseModel):
    email: EmailStr
    password: str
    

# Response payload (without password)
class UserResponseDTO(BaseModel):
    id: str
    userName: str
    email: str
    message: str

class LoginResponseDTO(BaseModel):
    token: str

class ChatRequest(BaseModel):
    user_question: str
