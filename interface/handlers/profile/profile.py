from fastapi import FastAPI, Request, Form, Body, APIRouter, Depends
from fastapi.security.api_key import APIKeyQuery, APIKeyCookie, APIKeyHeader, APIKey
from auth import GetApiKey
from typing import Optional
from pydantic import BaseModel
import time
from utils import Utilities
from dbUtils import DbUtils
import json
import copy

from handlers.models.user import User
from handlers.models.session import Session

from sqlalchemy import func

from database import SessionLocal
db = SessionLocal()

dbUtils = DbUtils()
utilities = Utilities()

router = APIRouter()

class UpdateBody(BaseModel):
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    # email: str = None
    # password: str = None
    cellphone: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[str]= None
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    address_postal_code: Optional[str] = None
    address_state: Optional[str] = None
    address_country: Optional[str] = None
    profile_pic: Optional[str] = None

class timeOffsetBody(BaseModel):
    time_offset: int = None

class PayFastBody(BaseModel):
    m_payment_id: Optional[str] = None
    pf_payment_id: Optional[int] = None
    payment_status: Optional[str] = None
    item_name: Optional[str]= None


@router.get("/user/profile")
def form_post(request: Request, api_key: APIKey = Depends(GetApiKey)):
    current_epoch_time = int(time.time())
    min_time =[]
    max_time =[]
    raw_user_info = None

    user_id = None
    try:
        session = db.query(Session).filter(Session.session_id == api_key).first()
        user_id = session.user_id
    except:
        db.rollback()
        message = "[Profile]: Failed to get session information"
        return utilities.failedMessage(message)
    
    try:
        # raw_user_info = dbUtils.getUserByAPIKey(api_key)
        raw_user_info = db.query(User).filter(User.user_id == user_id).first()
    except:
        db.rollback()
        message = "[Profile]: Failed to get user information"
        return utilities.failedMessage(message)

    try:
        # Assign user values
        user_id = raw_user_info.user_id
        username =raw_user_info.username
        email = raw_user_info.email
        firstname = raw_user_info.first_name
        surname = raw_user_info.last_name
        gender = raw_user_info.gender
        date_of_birth = raw_user_info.date_of_birth
        country = raw_user_info.country_of_birth
        cellphone = raw_user_info.cellphone_number
        last_login = raw_user_info.last_login
        # device_id = raw_user_info.device_id
        api_key = raw_user_info.api_key
        api_key_gen_time = raw_user_info.api_key_gen_time
        verification_link = raw_user_info.verification_link
        account_active = raw_user_info.account_active
        account_verified = raw_user_info.account_verified
        account_type = raw_user_info.account_type
        # reset pass toke =raw_user_info[18]
        profile_pic = raw_user_info.profile_pic
        cellphone_code =raw_user_info.cellphone_code
        cellphone_verified =raw_user_info.cellphone_verified
        time_offset =raw_user_info.time_offset
        address_line_1 = raw_user_info.address_line_1
        address_line_2 = raw_user_info.address_line_2
        address_postal_code = raw_user_info.address_postal_code
        address_state = raw_user_info.address_state
        address_country = raw_user_info.address_country
        whatsapp_messages = raw_user_info.whatsapp_messages
        sms_messages = raw_user_info.sms_messages
        api_calls = raw_user_info.api_calls
        
        if address_line_1 == None:
            address_line_1 = ""

        if address_line_2 == None:
            address_line_2 = ""

        if address_postal_code == None:
            address_postal_code = ""

        if address_state == None:
            address_state = ""

        # If time_offset is None, then set it to zero
        if time_offset == None:
            time_offset = 0
        else:
            time_offset = time_offset * 60
    except Exception as error:
        db.rollback()
        print(error)
        return utilities.failedMessage("[Profile] Failed to get profile:" +str(error))
    
    # Check if the min max is not null
    if not len(min_time):
        earliest_time = 0
    else:
        earliest_time =min(min_time)
    
    if not len(max_time):
        maximum_time = 2147483647 # max epoch time
    else:
        maximum_time = max(max_time)

    if whatsapp_messages == None:
        whatsapp_messages = 0

    if sms_messages == None:
        sms_messages = 0

    # Pack the response in json
    try:
        # Set the user account type strings
        if account_type == 1:
            # Basic
            account_type = "Basic (Free)"
        elif account_type == 2:
            # Start-up
            account_type = "Start-up"
        elif account_type == 3:
            # Growth
            account_type = "Growth"
        elif account_type == 4:
            # Premium
            account_type = "Premium"
        elif account_type == 5:
            # Enterprise
            account_type = "Enterprise"
        else:
            account_type = "Basic (Free)"

        user_info = {
                    "user_id": user_id,
                    "username": username,
                    "email": email,
                    "firstname": firstname,
                    "surname": surname,
                    "gender": gender,
                    "date_of_birth": date_of_birth,
                    "country": country,
                    "cellphone": cellphone,
                    "last_login": last_login,
                    "api_key": api_key,
                    "account_type": account_type,
                    "account_active": account_active,
                    "account_verified": account_verified,
                    "address_line_1": address_line_1,
                    "address_line_2": address_line_2,
                    "address_postal_code": address_postal_code,
                    "address_state" : address_state,
                    "address_country": address_country,
                    "profile_pic": profile_pic,
                    "cellphone_verified": cellphone_verified,
                    "whatsapp_messages": whatsapp_messages,
                    "sms_messages":sms_messages, 
                    "api_calls": api_calls
                }
        return utilities.successMessage(user_info)
        #return user_info
    except Exception:
        message = "Failed to get user info. Try to login again. "+ str()
        return utilities.failedMessage(message)

@router.post("/update/profile")
async def enable_alerts(api_key: APIKey = Depends(GetApiKey), params: UpdateBody = Depends(), payload: UpdateBody = Body(None)):
    current_epoch_time = int(time.time())
    
    # Get user account
    try:
        account = get_user_using_api_key(api_key)
        user_id = account.user_id
        time_offset = account.time_offset
    except Exception:
        message = "(A)Failed to get user info. Try to login again."
        return utilities.failedMessage(message)

    user_id = account.user_id
    username =account.username
    email = account.email
    firstname = account.first_name
    surname = account.last_name
    gender = account.gender
    date_of_birth = account.date_of_birth
    country = account.country_of_birth
    cellphone = account.cellphone_number
    last_login = account.last_login
    # device_id = raw_user_info.device_id
    api_key = account.api_key
    api_key_gen_time = account.api_key_gen_time
    verification_link = account.verification_link
    account_active = account.account_active
    account_verified = account.account_verified
    account_type = account.account_type
    # reset pass toke =raw_user_info[18]
    profile_pic = account.profile_pic
    cellphone_code =account.cellphone_code
    cellphone_verified =account.cellphone_verified
    time_offset =account.time_offset
    address_line_1 = account.address_line_1
    address_line_2 = account.address_line_2
    address_postal_code = account.address_postal_code
    address_state = account.address_state
    address_country = account.address_country
    whatsapp_messages = account.whatsapp_messages
    sms_messages = account.sms_messages

    # firstname
    if params.firstname != None:
        firstname = params.firstname
    elif payload != None and payload.firstname != None:
        firstname = payload.firstname
    else:
        firstname = firstname

    # lastname
    if params.lastname != None:
        lastname = params.lastname
    elif payload != None and payload.lastname != None:
        lastname = payload.lastname
    else:
        lastname = surname
    
    # cellphone
    if params.cellphone != None:
        cellphone = params.cellphone
    elif payload != None and payload.cellphone != None:
        cellphone = payload.cellphone
    else:
        cellphone = cellphone
    
    # gender
    if params.gender != None:
        gender = params.gender
    elif payload != None and payload.gender != None:
        gender = payload.gender
    else:
        gender = gender
    
    # date_of_birth
    if params.date_of_birth != None:
        date_of_birth = params.date_of_birth
    elif payload != None and payload.date_of_birth != None:
        date_of_birth = payload.date_of_birth
    else:
        date_of_birth = date_of_birth
    
    # address_line_1
    if params.address_line_1 != None:
        address_line_1 = params.address_line_1
    elif payload != None and payload.address_line_1 != None:
        address_line_1 = payload.address_line_1
    else:
        address_line_1 = address_line_1
    
    # address_line_2
    if params.address_line_2 != None:
        address_line_2 = params.address_line_2
    elif payload != None and payload.address_line_2 != None:
        address_line_2 = payload.address_line_2
    else:
        address_line_2 = address_line_2
    
    # address_postal_code
    if params.address_postal_code != None:
        address_postal_code = params.address_postal_code
    elif payload != None and payload.address_postal_code != None:
        address_postal_code = payload.address_postal_code
    else:
        address_postal_code = address_postal_code
    try:
        int(address_postal_code)
    except Exception as error:
        return utilities.failedMessage(str("Invalid type: Postal code has to be a valid integer"))
        
    # address_state
    if params.address_state != None:
        address_state = params.address_state
    elif payload != None and payload.address_state != None:
        address_state = payload.address_state
    else:
        address_state = address_state

    # address_country
    if params.address_country != None:
        address_country = params.address_country
    elif payload != None and payload.address_country != None:
        address_country = payload.address_country
    else:
        address_country = address_country

    # profile_pic
    if params.profile_pic != None:
        profile_pic = params.profile_pic
    elif payload != None and payload.profile_pic != None:
        profile_pic = payload.profile_pic
    else:
        address_country = address_country

    try:
        # Update the user
        # dbUtils.updateUser(firstname, lastname, gender, cellphone, date_of_birth, address_line_1, address_line_2,
        #               address_postal_code, address_state, address_country, profile_pic, user_id)
        account.first_name = firstname
        account.last_name = lastname
        account.gender = gender
        account.cellphone_number = cellphone
        account.date_of_birth = date_of_birth
        account.address_line_1 = address_line_1
        account.address_line_2 = address_line_2
        account.address_postal_code = address_postal_code
        account.address_state = address_state
        account.address_country = address_country
        account.profile_pic = profile_pic
        account.user_id = user_id

        db.add(account)
        db.commit()
        db.refresh(account)

        return utilities.successMessage("Successfully updated user info")
        
    except Exception as e:
        print(str(e))
        message = '(B)Failed to update account. ' + str(e)
        return utilities.failedMessage(message)

@router.post("/update/profile/offset")
async def update_time_offset(api_key: APIKey = Depends(GetApiKey), params: timeOffsetBody= Depends(), payload: timeOffsetBody = Body(None)):
    current_epoch_time = int(time.time())

    # Get user account
    try:
        account = get_user_using_api_key(api_key)
        user_id = account.user_id
        time_offset = account.time_offset
    except Exception:
        message = "(A)Failed to get user info. Try to login again."
        return utilities.failedMessage(message)

    # time_offset
    if params.time_offset != None:
        time_offset = params.time_offset
    elif payload != None and payload.time_offset != None:
        time_offset = payload.time_offset
    else:
        return utilities.failedMessage("Missing field: time_offset")

    # Update the user time offset
    try:
        
        # dbUtils.updateUserTimeOffset(user_id, time_offset)
        account.time_offset = time_offset
        db.add(account)
        db.commit()
        db.refresh(account)
        return utilities.successMessage("Successfully updated user time offset")
        
    except Exception as error:
        print(str(error))
        message = '(B)Failed to update time offset. ' + str(error)
        return utilities.failedMessage(message)

def get_user_using_api_key(api_key):
    try:
        session = db.query(Session).filter(Session.session_id == api_key).first()
        user_id = session.user_id
    except Exception as error:
        message = "[Profile]: Failed to get session information"
        print("[GET User] "+str(error))
        return utilities.failedMessage(message)

    try:
        # raw_user_info = dbUtils.getUserByAPIKey(api_key)
        raw_user_info = db.query(User).filter(User.user_id == user_id).first()
    except Exception as error:
        message = "[Profile]: Failed to get user information."
        print(str(error))
        return utilities.failedMessage(message)

    return raw_user_info