from fastapi import HTTPException
from uuid import uuid4

from constant.extra import get_user_by_email, hashPassword, save_user, verify_password

from jwt_Str.access import create_access_token
from services.user.dto import UserLoginDTO, UserResponseDTO, UserSignupDTO


class User_Service:
    def __init__(self):
        pass

    def signUp(self, signUp: UserSignupDTO):
        try:
            if get_user_by_email(signUp.email):
                raise HTTPException(status_code=400, detail="Email Already reg")
            user = {
                
                "userName": signUp.userName,
                "email": signUp.email,
                "password": hashPassword(signUp.password)
            }
            data = save_user(user)
            # return UserResponseDTO(
            #     id=user["id"],
            #     userName=user["userName"],
            #     email=user["email"],
            #     message="user Signup successful"
            # )
            return data

        except HTTPException as e:
            raise e
        except Exception as e:
            print(f"Signup error: {e}")
            raise HTTPException(status_code=500, detail="Failed to signup")
        
    def login(self, login: UserLoginDTO):
        user = get_user_by_email(login.email)
        print("user",user)
        if not user:
            raise HTTPException(status_code=404, detail='user not found')

        try:
            if not verify_password(login.password, user["password"]):
                raise HTTPException(status_code=400, detail="invalid password")

            # return UserResponseDTO(
            #     id=user["_id"],
            #     userName=user["userName"],
            #     email=user["email"],
            #     message='login sucessfull'
            # )
            return {"token" :create_access_token(data={"user_id":user['_id'], "email":user['email']})}
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"login failed {e}")

