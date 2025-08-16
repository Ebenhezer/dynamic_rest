import email
import json
import os, requests, re
import random
import datetime, time
from shutil import ExecError
import secrets
import hashlib
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

from dbUtils import DbUtils
dbUtils = DbUtils()

from handlers.models.config import Config
from database import SessionLocal
db = SessionLocal()

from handlers.models.user import User
from handlers.models.models import Interface
class Utilities:
    
    def failedMessage(self, message):
        results = {'failed': message}
        
        if "Incorrect username/password" in message:
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=results)
        elif "Try to login again" in message:
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=results)
        elif "Incorrect device information" in message:
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=results)
        elif "Invalid device information" in message:
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=results)
        else:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=results)
        # return results
    
    def successMessage(self, message):
        results = {'success': message}
        return results
    
    def statusCheck(self,update_time,update_period ):
        if update_time > update_period:
            switch_status = "Offline"
        else:
            switch_status = "Online"
        return switch_status
    
    def getCurrentEpoch(self):
        # Get current time
        current_epoch_time = int(time.time())
        return current_epoch_time
    
    def getId(self):
        # Generate a random number by concatinating the current epoch time and a random seven digit number
        #   between 100 and 900
        random_number = random.randint(100, 900)
        current_epoch_time = int(time.time())
        id = int(str(current_epoch_time) + str(random_number));
        return id
    
    def getDeviceTypeNumber(self, device_type):
        if (device_type == "switch"):   
            random_number = random.randint(10, 20)
        elif (device_type == "sensor"):
            random_number = random.randint(21, 30)
        elif (device_type == "ws"):
            random_number = random.randint(31, 40)
        elif (device_type == "gps"):
            random_number = random.randint(41, 50)
        elif (device_type == "met"):
            random_number = random.randint(51, 60)
        elif (device_type == "batmon"):
            random_number = random.randint(61, 70)
        elif (device_type == "device"):
            random_number = random.randint(71, 80)
        elif device_type == "interface" or device_type == "dynamic":
            random_number = random.randint(100, 150)
        else:
            random_number = random.randint(91, 999)
        
        return int(random_number)
    
    def getToken(self):
        token = secrets.token_hex(20)
        return token
    
    def getApiKey(self):
        token = secrets.token_hex(25)
        return token
    
    def hash_password(self, password):
        return hashlib.sha256(str.encode(password)).hexdigest()

    def check_hash(self, password, hash):
        if self.hash_password(password) == hash:
            #Password matches
            return True
        # Password don't match
        return False
    
    def get_ip_location(self, ip_address):
        url = f"https://ipapi.co/{ip_address}/json/"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            country = data.get('country_name')
            city = data.get('city')
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            # Retrieve other location details as needed
            # return f"Country: {country}, City: {city}, Latitude: {latitude}, Longitude: {longitude}"
            return f"Country: {country}, City: {city}"
        else:
            return "Location information not available"

    def is_valid_email(self, email: str) -> bool:
        return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None

    def is_valid_mobile(self, number: str) -> bool:
        # Very basic international format validator (starts with + and 10–15 digits)
        return re.fullmatch(r"^\+\d{10,15}$", number) is not None

    def parse_notifications(self, raw: dict):
        print(raw)
        try:
            notifications = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(f"Payload must be valid JSON: {str(e)}")

        if not isinstance(notifications, list):
            raise ValueError("Payload must be a list of objects.")

        validated = []
        for idx, n in enumerate(notifications):
            if not isinstance(n, dict):
                raise ValueError(f"Item at index {idx} must be a JSON object.")

            # Name
            name = n.get("name")
            if name is not None and not isinstance(name, str):
                raise ValueError(f"'name' at index {idx} must be a string.")

            # Email
            email = n.get("email")
            if not email:
                raise ValueError(f"'email' is required at index {idx}.")
            if not self.is_valid_email(email):
                raise ValueError(f"'email' at index {idx} is invalid: '{email}'")

            # Boolean fields
            for field in ["threshold_alerts", "status_alerts", "sms_alerts", "whatsapp_alerts"]:
                value = n.get(field)
                if value is not None and not isinstance(value, bool):
                    raise ValueError(f"'{field}' at index {idx} must be true or false (boolean).")

            sms_alerts = n.get("sms_alerts", False)
            whatsapp_alerts = n.get("whatsapp_alerts", False)

            # Validate mobile_number only if alerts are on
            mobile_number = n.get("mobile_number")
            if (sms_alerts or whatsapp_alerts):
                if not mobile_number:
                    raise ValueError(f"'mobile_number' is required at index {idx} when sms_alerts or whatsapp_alerts are true.")
                if not self.is_valid_mobile(mobile_number):
                    raise ValueError(f"'mobile_number' at index {idx} is invalid: must start with '+' and include country code (e.g., +27831234567).")

            validated.append({
                "name": name,
                "email": email,
                "threshold_alerts": bool(n.get("threshold_alerts", False)),
                "status_alerts": bool(n.get("status_alerts", False)),
                "sms_alerts": bool(sms_alerts),
                "whatsapp_alerts": bool(whatsapp_alerts),
                "mobile_number": mobile_number
            })

        return validated
    
    def increment_user_api_calls(self, user_id: int):
        from sqlalchemy.orm import Session
        from database import SessionLocal

        db: Session = SessionLocal()

        try:
            user = db.query(User).filter(User.user_id == user_id).first()
            if user:
                if user.api_calls == None:
                    user.api_calls = 1
                else:
                    user.api_calls = user.api_calls  + 1
                db.commit()
            else:
                print(f"User {user_id} not found.")
        except Exception as e:
            db.rollback()
            print(f"Error incrementing API calls: {e}")
        finally:
            db.close()