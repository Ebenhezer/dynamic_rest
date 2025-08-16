from fastapi import FastAPI, Request, Form, Body, APIRouter, Security, HTTPException, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Depends, Body, Request, File, UploadFile, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.security.api_key import APIKeyQuery, APIKeyCookie, APIKeyHeader, APIKey
from fastapi.responses import JSONResponse
from starlette.status import HTTP_403_FORBIDDEN
from typing import Optional
from sqlalchemy import cast, String

from fastapi import FastAPI, Request, Form, Body, APIRouter, Depends
from fastapi.security.api_key import APIKeyQuery, APIKeyCookie, APIKeyHeader, APIKey
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import time
from utils import Utilities
from dbUtils import DbUtils

from config import logger
from handlers.models.user import User
from handlers.models.notifications import Notification
from handlers.models.session import Session
from database import SessionLocal
db = SessionLocal()

router = APIRouter()
dbUtils = DbUtils()
utilities = Utilities()

class LoginDetails(BaseModel):
    username: str = None
    password: str = None

class RegisterProfile(BaseModel):
    firstname: str = None
    lastname: str = None
    email: str = None
    password: str = None
    cellphone: str = None
    gender: Optional[str] = None
    date_of_birth: str= None
    address_line_1: str = None
    address_line_2: Optional[str] = None
    address_postal_code: int = None
    address_state: str = None
    address_country: str = None
    profile_pic: str = None

api_key_cookie = APIKeyCookie(name="api_key", auto_error=False)
api_key_query = APIKeyQuery(name="api_key", auto_error=False)

def GetApiKey(api_key_cookie: str = Security(api_key_cookie), api_key_query: str = Security(api_key_query)):
    if api_key_query != None:
        # First verify that the user API key is valid
        try:
            session = db.query(Session).filter(Session.session_id == api_key_query).first()
        except Exception as error:
            print("Failed to validate access_token" +str(error))
        
        try:
            if session:
                return api_key_query
            else:
                message = "[Auth]: Failed to validate the api_key/access_token. Try to login again."
                return utilities.failedMessage(message)
            
        except Exception as error:
            print("Failed to validate access_token" +str(error))
            return utilities.failedMessage("[Auth]: Failed to validate the api_key/access_token. Please try again.")

        
    elif api_key_cookie != None:
        # First verify that the user API key is valid
        try:
            session = db.query(Session).filter(Session.session_id == api_key_cookie).first()
        except Exception as error:
            print("Failed to validate access_token" +str(error))
        
        if session:
            return api_key_cookie
        else:
            message = "[Auth]: Failed to validate the api_key/access_token. Try to login again."
            return utilities.failedMessage(message)
    else:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Not authenticatted.")
        

@router.post("/login", tags=["Authentication"])
def token_generate(request: Request, payload: LoginDetails):
    api_key = utilities.getToken()
    current_epoch_time = int(time.time())
    
    username = payload.username
    password = payload.password
    
    # Check if account exists using MySQL
    try:
        hashed_password = utilities.hash_password(password)
        account = db.query(User).filter(User.username.like(username), User.user_password.like(hashed_password)).first()
    except Exception as e:
        message = 'Failed to hash'
        logger.error("Error: ", str(e))
        return utilities.failedMessage("Failed to login: "+str(e))

    # Check if the email account has been verified, if not, the render a failed message to indicate that email is not verified
    # Index 16 is the account_verified boolfield.
    if account:
        email_address = account.email
        firstname = account.first_name
        token = account.verification_link
        account_verified = account.account_verified
        user_id = account.user_id
        verification_sent = False
    else:
        # Account doesnt exist or username/password incorrect
        message = 'Incorrect username/password! or user does not exists'
        return utilities.failedMessage(message)

    if account_verified == None or account_verified == False:
        verification_sent = True    
        message ="Please verify your email. A verification link has been sent to: "+ email_address  
        response = {
            "account_verified": False,
            "verification_sent": verification_sent ,
            "message": message
        }

        return utilities.failedMessage(response)
    
    # If the account exists, the set the session attributes
    if account:
        # Update the user's API key
        try:
            content = {"access_token": api_key}
            response = JSONResponse(content=content)
            response.set_cookie(key="api_key", value=api_key,
                                max_age=1800, expires=1800)
        except Exception:
            message = "Failed to update the key"
            logger.error("Failed to update the key")
            return utilities.failedMessage(message)
    else:
        # Account doesnt exist or username/password incorrect
        message = 'Incorrect username/password!'
        return utilities.failedMessage(message)

    try:
        request_user_agent = request.headers.get("User-Agent")
        request_ip_address = request.headers.get('X-Real-IP')
        sessions = db.query(Session).filter(Session.user_id == user_id).all()
        session_found = False
        for session in sessions:
            # If the user host IP and agent are the same. Then we can assume that they are using the same device. So we just update the existing record
            if str(session.user_agent) == str(request_user_agent) and str(session.session_ip_address) == str(request_ip_address):
                s = db.query(Session).filter(Session.session_id == session.session_id).first()
                s.session_id = api_key
                s.session_ip_address = request.headers.get('X-Real-IP')
                s.session_start_time = current_epoch_time
                s.session_status = True
                s.user_agent = request.headers.get("User-Agent")
                s.device_type = ""
                s.session_location = utilities.get_ip_location(request_ip_address)
                s.referrer = request.headers.get("Referer")

                db.add(session)
                db.commit()
                db.refresh(session)
                
                session_found = True
        
        if session_found == False:
            session = Session()
            session.user_id = user_id
            session.session_id = api_key
            session.session_ip_address = request.headers.get('X-Real-IP')
            session.session_start_time = current_epoch_time
            session.session_status = True
            session.user_agent = request.headers.get("User-Agent")
            session.device_type = ""
            session.session_location = utilities.get_ip_location(request_ip_address)
            session.referrer = request.headers.get("Referer")

            db.add(session)
            db.commit()
            db.refresh(session)
            
    except Exception as error:
        print("failed to add session info to session table. "+str(error))
        logger.error("failed to add session info to session table. "+str(error))
    
    return response

@router.post("/signup", tags=["Authentication"])
def signup(payload: RegisterProfile):
    current_epoch_time = int(time.time())
    user_registered = False
    notification_sent = False

    firstname = payload.firstname 
    lastname = payload.lastname
    email = payload.email
    gender = payload.gender
    cellphone = payload.cellphone
    password = payload.password
    date_of_birth = payload.date_of_birth
    address_line_1 = payload.address_line_1
    address_line_2 = payload.address_line_2
    address_postal_code = payload.address_postal_code
    address_state = payload.address_state
    address_country = payload.address_country
    profile_pic = payload.profile_pic

    if firstname == None or firstname == "":
        return utilities.failedMessage("Missing body argument: firstname")
    elif lastname == None or lastname == "":
        return utilities.failedMessage("Missing body argument: lastname")
    elif email == None or email == "":
        return utilities.failedMessage("Missing body argument: email")
    elif cellphone == None or cellphone == "":
        return utilities.failedMessage("Missing body argument: cellphone")
    elif password == None or password == "":
        return utilities.failedMessage("Missing body argument: password")
    elif date_of_birth == None:
        date_of_birth = "None"
    # elif gender == None or gender == "":
    #     return utilities.failedMessage("Missing body argument: gender")
        # return utilities.failedMessage("Missing body argument: date_of_birth")
    # elif address_line_1 == None:
    #     return utilities.failedMessage("Missing body argument: address_line_1")
    # elif address_line_2 == None:
    #     return utilities.failedMessage("Missing body argument: address_line_2")
    # elif address_postal_code == None:
    #     return utilities.failedMessage("Missing body argument: address_postal_code")
    # elif address_state == None:
    #     return utilities.failedMessage("Missing body argument: address_state")
    # elif address_country == None:
    #     return utilities.failedMessage("Missing body argument: address_country")
    # elif profile_pic == None:
    #     return utilities.failedMessage("Missing body argument: profile_pic")

    # Firstly check if the email account exist
    try:
        account = dbUtils.getUserByEmail(email)
        if account is not None:
            message = 'Username already exists'
            return utilities.failedMessage(message)
    except Exception as e:
        print(e)
        message = '(A)Failed to register account. ' +str(e)
        logger.error(message)
        return utilities.failedMessage(message)

    api_key = utilities.getApiKey()
    #token = s.dumps(email, salt='email-confirm')
    token = utilities.getToken()

    # Hash the password
    hashed_password = utilities.hash_password(password)
    try:
        # Add the user into the database
        verification_link = token
        db_user = User()
        db_user.first_name = firstname
        db_user.last_name = lastname
        db_user.username = email
        db_user.email = email
        db_user.user_password = hashed_password
        db_user.gender = gender
        db_user.cellphone_number = cellphone
        db_user.date_of_birth = date_of_birth
        db_user.address_line_1 = address_line_1
        db_user.address_line_2 = address_line_2
        db_user.address_postal_code = address_postal_code
        db_user.address_state = address_state
        db_user.address_country = address_country
        db_user.profile_pic = profile_pic
        db_user.account_verified = True
        db_user.api_key = api_key
        db_user.verification_link = verification_link
        db_user.last_login = current_epoch_time

        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        user_registered = True
        
    except Exception as e:
        user_registered = False
        print(str(e))
        message = '(B)Failed to register account.' + str(e)
        logger.error(message)
        return utilities.failedMessage(message)
    
    # Send verification e-mail 
    try:
        notification_sent = True
    except Exception as e:
        logger.error(str(e))
        notification_sent = False
        
    message = {
        "user_registered": user_registered ,
        "access_token": api_key,
        "notification_sent": notification_sent
    }
    return utilities.successMessage(message)

@router.post("/logout", tags=["Authentication"])
def logout(request: Request, api_key: APIKey = Depends(GetApiKey)):
    
    # Clear the database key
    try:
        logout_response = dbUtils.LogoutApiKey(api_key)
    except Exception as error:
        logger.error(str(error))
        print("Failed to logout. " +str(error))
    
    try:
        db.query(Session).filter(Session.session_id == api_key).delete()
        db.commit()
    except Exception as error:
        print("Failed to delete session")

    # Clear the cookie
    content = {"message": "Logged out"}
    response = JSONResponse(content=content)
    response.delete_cookie("api_key")
    return response

@router.get("/sessions", tags=["Authentication"])
def session(request: Request, api_key: APIKey = Depends(GetApiKey)):
    sessions = None
    # Get user information
    try:
        # raw_user_info = dbUtils.getUserByAPIKey(api_key)
        raw_user_info = db.query(Session).filter(Session.session_id == api_key).first()
    except:
        message = "Failed to get user information"
        return utilities.failedMessage(message)
    
    user_id = raw_user_info.user_id
    try:
        sessions = db.query(Session).filter(Session.user_id == user_id).all()
    except Exception as error:
        logger.error(str(error))
        print("Failed to get all sessions" +str(error))

    arr_sessions = []
    if sessions:
        for session in sessions:
            user_info = db.query(User).filter(User.user_id == user_id).first()
            time_offset = user_info.time_offset
            if time_offset == None:
                time_offset = 0

            session_start_time = session.session_start_time
            session_end_time = session.session_duration

            if session_start_time != None:
                session_start_time = session_start_time + time_offset*60 # Apply offset 

            if session_end_time != None:
                session_end_time = session_end_time + time_offset*60 # Apply offset 
                
            data = {
                "user_agent": session.user_agent,
                "referrer": session.referrer,
                "session_status": session.session_status,
                "session_error_log": session.session_error_log,
                "session_start_time": session_start_time,
                "session_end_time": session_end_time,
                "session_duration": session.session_duration,
                "device_type": session.device_type,
                "session_location": session.session_location,
                "session_data": session.session_data,
                "session_id": session.session_id,
                "session_ip_address": session.session_ip_address
            }
            arr_sessions.append(data)
            
        return utilities.successMessage(arr_sessions)
    else:
        message = "Failed to get user information"
        return utilities.failedMessage(message)

