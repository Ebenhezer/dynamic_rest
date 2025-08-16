from fastapi import FastAPI, Request, Form, Body, APIRouter, Depends
from fastapi.security.api_key import APIKeyQuery, APIKeyCookie, APIKeyHeader, APIKey
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from auth import GetApiKey
from typing import Optional
import re
import datetime
import time
from utils import Utilities
from dbUtils import DbUtils
import json
import copy
from sqlalchemy import text
from time import sleep
from typing import List
from handlers.models.user import User
from handlers.models.notifications import Notification
from handlers.models.models import Interface
from handlers.profile.profile import get_user_using_api_key

from handlers.models.models import create_dynamic_table
from sqlalchemy import or_, create_engine, MetaData, Table, Column, Integer, String, Boolean, inspect
from database import engine, metadata

from sqlalchemy.orm import Session
from database import SessionLocal

dbUtils = DbUtils()
utilities = Utilities()

router = APIRouter()

class FieldModel(BaseModel):
    field_name: str
    field_type: str
    trendable: bool
    required: bool
class BodyModel(BaseModel):
    interface_url: Optional[str] = Body(None)
    interface_description: Optional[str] = Body(None)
    interface_token: Optional[str] = Body(None)
    fields: Optional[List[FieldModel]] = Body(None)
    update_period: Optional[int] = Body(None)
    table_name: Optional[str] = Body(None)
    update_period: Optional[int] = Body(None)

class ParamsModel(BaseModel):
    interface_url: Optional[str] = None
    interface_description: Optional[str] = None
    interface_token: Optional[str] = None
    fields: Optional[List[FieldModel]] = None
    table_name: Optional[str] = None
    update_period: Optional[int] = None

class EditBodyModel(BaseModel):
    interface_id: Optional[int] = Body(None)
    interface_url: Optional[str] = Body(None)
    interface_token: Optional[str] = Body(None)
    interface_description: Optional[str] = Body(None)
    fields: Optional[List[FieldModel]] = Body(None)
    last_modified: Optional[int] = Body(None)
    update_period: Optional[int] = Body(None)
    notification_users: Optional[str] = Body(None)
    notification_enabled: Optional[bool] = Body(None)
    whatsapp_enabled: Optional[bool] = Body(None)
    sms_enabled: Optional[bool] = Body(None)
    # table_name: Optional[str] = Body(None)

class DeleteBodyModel(BaseModel):
    interface_id: Optional[int] = Body(None)
    
class DeleteFieldBodyModel(BaseModel):
    interface_id: Optional[int] = Body(None)
    field_name: Optional[str] = Body(None)

allowed_field_types = ["Integer", "String", "Boolean"]

@router.post("/dynamic", tags=['Dynamic Endpoint'])
async def add_interface_data(request: Request, api_key: APIKey = Depends(GetApiKey), params: ParamsModel = Depends(), payload: BodyModel = Body()):
    current_epoch_time = int(time.time())
    # Create a new database session
    db: Session = SessionLocal()
    try:
        # Get user account
        try:
            account = get_user_using_api_key(api_key)
            print(account)
            user_id = account.user_id
            account_type = account.account_type
        except Exception as error:
            message = "(A)Failed to get user info. Try to login again. "+str(error)
            return utilities.failedMessage(message)
        
        try:
            # Endpoint name or url
            interface_url = None
            if params.interface_url:
                interface_url = params.interface_url
            elif payload != None:
                if payload.interface_url:
                    interface_url = payload.interface_url
            else:
                message = "Missing field: interface_url"
                return utilities.failedMessage(message)

            #Interface update period
            if params.update_period != None:
                update_period = params.update_period
            elif payload != None and payload.update_period != None:
                update_period = payload.update_period
            else:
                message = "Missing field: update_period"
                return utilities.failedMessage(message)
            
            #Interface token 
            interface_token = None
            if params.interface_token != None:
                interface_token = params.interface_token
            elif payload != None and payload.interface_token != None:
                interface_token = payload.interface_token
            
            #Check if the user has specififed the token, if not, generate a random one
            if interface_token == None:
                interface_token = utilities.getToken()

            pattern = r'^/[\w/]*$'
            if not re.match(pattern, interface_url):
                print("Invalid field: interface_url. URL should start with '/'")
                message = "Invalid field: interface_url. URL should start with '/'"
                return utilities.failedMessage(message)
            
            # Check if the URL already exists
            interface_url_with_slash = "/"+interface_url
            interface_url_exists = db.query(Interface).filter(or_(Interface.interface_url == interface_url, Interface.interface_url == interface_url_with_slash)).first()
            if interface_url_exists != None:
                message = "Failed to create interface. URL already exists."
                return utilities.failedMessage(message)
            
            # Description
            interface_description = None
            if payload != None:
                if payload.interface_description:
                    interface_description = payload.interface_description
            if interface_description == None:
                message = "Missing field: interface_description"
                return utilities.failedMessage(message)
            
            # Table name
            table_name = None
            if payload != None:
                if payload.table_name:
                    table_name = payload.table_name

            if table_name == None:
                message = "Missing field: table_name"
                return utilities.failedMessage(message)
            
            # Fields list
            fields = None
            if payload != None:
                if payload.fields:
                    fields = payload.fields

            if fields == None:
                message = "Missing field: fields"
                return utilities.failedMessage(message)

            #TODO: If not required, maybe have a default value option
            
            if not isinstance(fields, list):
                message = "Invalid field: fields. Field must be an a list of object."
                return utilities.failedMessage(message)
            
            interface_columns = {}
            for field in fields:
                if field.field_type in allowed_field_types:
                    interface_columns[field.field_name] = field.field_type
                else:
                    message = "Failed to validate the data type for: " +str(field.field_name)
                    return utilities.failedMessage(message)
            
            if interface_columns.get("epoch_time") == None:
                interface_columns["epoch_time"] = "Integer"
                
            # Create a dynamic table object based on the request
            try:
                dynamic_table = create_dynamic_table(table_name, interface_columns, False)
            except Exception as error:
                message = "Failed to create table: " +str(error)
                return utilities.failedMessage(message)

            # Create the table in the database if it doesn't exist
            table_created = False
            inspector = inspect(engine)
            if not inspector.has_table(table_name):
                dynamic_table.__table__.create(bind=engine)
                table_created = True
            else:
                message = "Failed to create table. Table name already exists."
                return utilities.failedMessage(message)
            
            if table_created == True:
                arr_json_fields = []
                interface_id = utilities.getId()
                try:
                    interface = Interface()
                    interface.interface_id = interface_id
                    interface.interface_url = interface_url
                    interface.interface_token = interface_token
                    interface.interface_description = interface_description
                    interface.table_name = table_name
                    interface.interface_owner = user_id
                    interface.last_modified = current_epoch_time
                    interface.update_period = update_period

                    for field in fields:
                        json_field = {
                            "field_name": field.field_name,
                            "field_type": field.field_type,
                            "trendable": field.trendable,
                            "required": field.required,
                        }

                        arr_json_fields.append(json_field)

                    # We also want to add a mandory field 'epoch_time'. So we first check if there is an epoch_time field in the fields 
                    has_epoch_time = any("epoch_time" in arr for arr in arr_json_fields)
                    if has_epoch_time == False:
                        arr_json_fields.append({
                            "field_name": "epoch_time",
                            "field_type": "Integer",
                            "trendable": False,
                            "required": False,
                        })

                    interface.fields = arr_json_fields

                    db.add(interface)
                    db.commit()
                    db.refresh(interface)
                    metadata.clear()
                    message = {
                        "interface_id": interface_id,
                        "interface_url": interface_url
                    }

                    utilities.increment_user_api_calls(user_id)
                    return utilities.successMessage(message)
                
                except Exception as error:
                    message = "(D) Failed to add a new interface. "+str(error)
                    return utilities.failedMessage(message)
            else:
                message = "Unable to create table."
                return utilities.failedMessage(message)
            
        except Exception as error:
            message = "(D)Failed to create dynamic endpoint. "+str(error)
            return utilities.failedMessage(message)
    finally:
        db.close()

@router.put("/dynamic", tags=['Dynamic Endpoint'])
async def update_interface_data(request: Request, api_key: APIKey = Depends(GetApiKey), payload: EditBodyModel = Body()):
    current_epoch_time = int(time.time())

    # Create a new database session
    db: Session = SessionLocal()
    try:
        # Get user account
        try:
            account = get_user_using_api_key(api_key)
            user_id = account.user_id
            account_type = account.account_type
        except Exception:
            message = "(A)Failed to get user info. Try to login again."
            return utilities.failedMessage(message)
        
        try:
            # Endpoint ID
            interface_id = None
            if payload != None:
                if payload.interface_id:
                    interface_id = payload.interface_id

            if interface_id == None:
                message = "Missing field: interface_id"
                return utilities.failedMessage(message)
            
            interface = db.query(Interface).filter(Interface.interface_id == interface_id).first()
            if interface == None:
                message = "Failed to find interface."
                return utilities.failedMessage(message)
            
            old_interface_fields = interface.fields
            
            # Endpoint name or url
            interface_url = None
            if payload != None:
                if payload.interface_url:
                    interface_url = payload.interface_url

            if interface_url != None:
                pattern = r'^/[\w/]*$'
                if not re.match(pattern, interface_url):
                    print("Invalid field: interface_url. URL should start with '/'")
                    message = "Invalid field: interface_url. URL should start with '/'"
                    return utilities.failedMessage(message)
                
                # Check if the URL already exists
                interface_url_with_slash = "/"+interface_url
                interface_url_exists = db.query(Interface).filter(or_(Interface.interface_url == interface_url, Interface.interface_url == interface_url_with_slash)).first()
                if interface_url_exists != None:
                    message = "Failed to create interface. URL already exists."
                    return utilities.failedMessage(message)
                
                interface.interface_url = interface_url
            
            # Description
            interface_description = None
            if payload != None:
                if payload.interface_description:
                    interface_description = payload.interface_description

            if interface_description != None:
                interface.interface_description = interface_description

            # Token
            interface_token = None
            if payload != None:
                if payload.interface_token:
                    interface_token = payload.interface_token

            if interface_token != None:
                interface.interface_token = interface_token
            
            # Update period
            update_period = None
            if payload != None:
                if payload.update_period:
                    update_period = payload.update_period

            if update_period != None:
                interface.update_period = update_period
                
            # Email Notifications
            if payload is not None and payload.notification_users:
                raw_notifications = payload.notification_users
            else:
                raw_notifications = None

            # Notification enabled
            notification_enabled = None
            if payload is not None and payload.notification_enabled:
                interface.notification_enabled = payload.notification_enabled

            # Whatsapp enabled
            whatsapp_enabled = None
            if payload is not None and payload.whatsapp_enabled:
                interface.whatsapp_enabled = payload.whatsapp_enabled
                
            
            # SMS enabled
            sms_enabled = None
            if payload is not None and payload.sms_enabled:
                interface.sms_enabled = payload.sms_enabled
            
            # Validate and parse
            if raw_notifications:
                try:
                    interface.notification_users = utilities.parse_notifications(raw_notifications)
                except ValueError as ve:
                    return utilities.failedMessage(f"Validation error in notification_users: {str(ve)}")
                except Exception as e:
                    return utilities.failedMessage(f"Unexpected error while parsing notification_users: {str(e)}")

            # # Table name
            # table_name = None
            # if payload != None:
            #     if payload.table_name:
            #         table_name = payload.table_name

            # if table_name != None:
            #     interface.table_name = table_name
            
            # Fields list
            fields = None
            if payload != None:
                if payload.fields:
                    fields = payload.fields

            if fields != None:
                if not isinstance(fields, list):
                    message = "Invalid field: fields. Field must be an a list of object."
                    return utilities.failedMessage(message)
            
                interface_columns = {}
                for field in fields:
                    if field.field_type in allowed_field_types:
                        interface_columns[field.field_name] = field.field_type
                    else:
                        message = "Failed to validate the data type for: " +str(field.field_name)
                        return utilities.failedMessage(message)

                # Create a json object for the db
                arr_json_fields = []
                for field in fields:
                    json_field = {
                        "field_name": field.field_name,
                        "field_type": field.field_type,
                        "trendable": field.trendable,
                        "required": field.required,
                    }

                    arr_json_fields.append(json_field)

                # We also want to add a mandory field 'epoch_time'. So we first check if there is an epoch_time field in the fields 
                has_epoch_time = any(field.get("field_name") == "epoch_time" for field in arr_json_fields)

                if has_epoch_time == False:
                    arr_json_fields.append({
                        "field_name": "epoch_time",
                        "field_type": "Integer",
                        "trendable": False,
                        "required": False,
                    })
                interface.fields = arr_json_fields
        except Exception as error:
            message = "Failed to validate fields: " +str(error)
            return utilities.failedMessage(message)

        # Create a MetaData object
        metadata = MetaData()

        # Define the name of the table you want to delete
        table_name = interface.table_name  # Replace with the name of the table you want to delete

        # Create a Table object for the table you want to delete
        table = Table(table_name, metadata, autoload_with=engine)

        # Check which fields no longer exist the new structure and remove them from the table
        fields_to_drop = []
        fields_to_add = []

        # Extract field names from both the old and new arrays
        field_names_old= set(item['field_name'] for item in old_interface_fields)
        field_names_new= set(item['field_name'] for item in arr_json_fields)

        # Check if field names from old exist in new. If not then we need to drop the field
        try:
            for field_name in field_names_old:
                if field_name in field_names_new:
                    print(f"'{field_name}' exists in both new.")
                else:
                    # print(f"'{field_name}' does not exist in new.")
                    fields_to_drop.append(field_name)

            for field in fields_to_drop:
                # Drop the column
                with engine.connect() as connection:
                    connection.execute(f"ALTER TABLE {table_name} DROP COLUMN {field}")
        except Exception as error:
            if not "does not exist":
                message = "Failed to drop fields: " +str(error)
                return utilities.failedMessage(message)
        
        # Check if field names from new exist in old. If not then we need to add the field
        try:
            for field_name in field_names_new:
                if field_name in field_names_old:
                    print(f"'{field_name}' exists in both.")
                else:
                    # print(f"'{field_name}' does not exist in old.")
                    fields_to_add.append(field_name)

            type_map = {
                "Integer": "INTEGER",
                "String": "VARCHAR(255)",
                "Text": "VARCHAR(255)",
                "Boolean": "BOOLEAN"
            }

            for field in fields_to_add:
                # Initialize variables
                new_column_name = None
                new_column_type = None

                # Find the field in your JSON array
                for column in arr_json_fields:
                    if column.get("field_name") == field:
                        new_column_name = column.get("field_name")
                        new_column_type = type_map.get(column.get("field_type"))

                # Add the column if both name and type are valid
                if new_column_name and new_column_type:
                    sql = f"ALTER TABLE {table_name} ADD COLUMN {new_column_name} {new_column_type}"
                    with engine.connect() as connection:
                        connection.execute(text(sql))
                        connection.commit()

        except Exception as error:
            message = "Failed to add new fields: " +str(error)
            return utilities.failedMessage(message)

        try:
            db.add(interface)
            db.commit()
            db.refresh(interface)
            metadata.clear()
            message = "Successfully updated the interface."

            utilities.increment_user_api_calls(user_id)
            return utilities.successMessage(message)
        except Exception as error:
            message = "Failed to update interface: " +str(error)
            return utilities.failedMessage(message)
    finally:
        db.close()

@router.get("/dynamic", tags=['Dynamic Endpoint'])
async def get_interface_data(request: Request, api_key: APIKey = Depends(GetApiKey)):
    current_epoch_time = int(time.time())
    # Create a new database session
    db: Session = SessionLocal()
    try:
        # Get user account
        try:
            account = get_user_using_api_key(api_key)
            user_id = account.user_id
            account_type = account.account_type
        except Exception as error:
            message = "(A) Failed to get user info. Try to login again. "+str(error)
            return utilities.failedMessage(message)
        
        # Get user info by switch_owner
        user_info = db.query(User).filter(User.user_id == user_id).first()
        time_offset = user_info.time_offset
        if time_offset == None:
            time_offset = 0

        # Get all the interfaces for the user
        interfaces = db.query(Interface).filter(Interface.interface_owner == user_id).all()
        results_data = []
        try:
            for interface in interfaces:
                last_modified = interface.last_modified
                # Status logic
                update_period = interface.update_period
                update_time = current_epoch_time - last_modified
                interface_status = utilities.statusCheck(update_time, update_period)
                # Before we return the time let's offset it
                if last_modified != None:
                    last_modified = last_modified + time_offset*60  # Apply offset

                # get device alarms
                # alarms = opGetAlarm(interface.interface_id)
                notification_users = interface.notification_users
                if interface.notification_users == None:
                    notification_users = []

                json_data = {
                    "interface_url": interface.interface_url,
                    "interface_id": interface.interface_id,
                    "interface_status": interface_status,
                    "interface_description": interface.interface_description,
                    "table_name": interface.table_name,
                    "interface_token": interface.interface_token,
                    "interface_details": interface.interface_details,
                    "update_period": update_period,
                    "last_modified": last_modified,
                    "notification_enabled": interface.notification_enabled,
                    "whatsapp_enabled": interface.whatsapp_enabled,
                    "sms_enabled": interface.sms_enabled,
                    "notification_users": notification_users,
                    # "alarms": alarms,
                    # "actual_update_time": interface.actual_update_time,
                    "fields": interface.fields
                }
            
                results_data.append(json_data)
        except Exception as error:
            message = "Failed to get interface information: "+str(error)
            return utilities.failedMessage(message)
        
        return utilities.successMessage(results_data)
    finally:
        db.close()

@router.delete("/dynamic", tags=['Dynamic Endpoint'])
async def delete_interface_data(request: Request, api_key: APIKey = Depends(GetApiKey), payload: DeleteBodyModel = Body()):
    current_epoch_time = int(time.time())
    # Create a new database session
    db: Session = SessionLocal()
    try:
        # Get user account
        try:
            account = get_user_using_api_key(api_key)
            user_id = account.user_id
            account_type = account.account_type
        except Exception:
            message = "(A)Failed to get user info. Try to login again."
            return utilities.failedMessage(message)
        
        try:
            # Endpoint ID
            interface_id = None
            if payload != None:
                if payload.interface_id:
                    interface_id = payload.interface_id

            if interface_id == None:
                message = "Missing field: interface_id"
                return utilities.failedMessage(message)
            
            interface = db.query(Interface).filter(Interface.interface_id == interface_id).first()
            if interface == None:
                message = "Failed to find interface."
                return utilities.failedMessage(message)
            
            # Create a MetaData object
            metadata = MetaData()

            # Define the name of the table you want to delete
            table_name = interface.table_name  # Replace with the name of the table you want to delete

            # Create a Table object for the table you want to delete
            table = Table(table_name, metadata, autoload_with=engine)

            # Drop the table
            metadata.reflect(bind=engine)
            table = metadata.tables.get(table_name)

            table.drop(engine)
            metadata.remove(table) 
            db.commit()
            db.query(Interface).filter(Interface.interface_id == interface_id).delete()
            db.commit()
            message = "Successfully deleted the interface."
            metadata.clear()
            utilities.increment_user_api_calls(user_id)
            return utilities.successMessage(message)
        except Exception as error:
            message = "Failed to delete interface: "+ str(error)
            return utilities.failedMessage(message)
    finally:
        db.close()
    
@router.delete("/dynamic/field/", tags=['Dynamic Endpoint'])
async def delete_interface_field(request: Request, api_key: APIKey = Depends(GetApiKey), payload: EditBodyModel = Body()):
    current_epoch_time = int(time.time())
    # Create a new database session
    db: Session = SessionLocal()
    try:
        # Get user account
        try:
            account = get_user_using_api_key(api_key)
            user_id = account.user_id
            account_type = account.account_type
        except Exception:
            message = "(A)Failed to get user info. Try to login again."
            return utilities.failedMessage(message)
        
        try:
            # Endpoint ID
            interface_id = None
            if payload != None:
                if payload.interface_id:
                    interface_id = payload.interface_id

            if interface_id == None:
                message = "Missing field: interface_id"
                return utilities.failedMessage(message)
            
            # Endpoint ID
            field_name = None
            if payload != None:
                if payload.field_name:
                    field_name = payload.field_name

            if field_name == None:
                message = "Missing field: field_name"
                return utilities.failedMessage(message)
            
            interface = db.query(Interface).filter(Interface.interface_id == interface_id).first()
            if interface == None:
                message = "Failed to find interface."
                return utilities.failedMessage(message)
            
            old_interface_fields = interface.fields

            # Create a MetaData object
            metadata = MetaData()

            # Define the name of the table you want to delete
            table_name = interface.table_name  # Replace with the name of the table you want to delete

            # Create a Table object for the table you want to delete
            table = Table(table_name, metadata, autoload=True, autoload_with=engine)
            # Check if field names from old exist in new. If not then we need to drop the field
            try:
                with engine.connect() as connection:
                    connection.execute(f"ALTER TABLE {table_name} DROP COLUMN {field_name}")
            except Exception as error:
                if not "does not exist":
                    message = "Failed to drop fields: " +str(error)
                    return utilities.failedMessage(message)

            message = "Successfully deleted the interface."
            metadata.clear()

            utilities.increment_user_api_calls(user_id)
            return utilities.successMessage(message)
        except Exception as error:
            message = "Failed to delete interface: "+ str(error)
            return utilities.failedMessage(message)
    finally:
        db.close()
    
@router.get("/dynamic/interface/{interface_url}" , tags=['Dynamic Endpoint'])
async def get_interface_info(interface_url: str, api_key: APIKey = Depends(GetApiKey)):
    """Function used to get interface information

    Parameters
    ----------
    interface_url : str
        The interface url that was created in the add method

    Returns
    -------
    dict
        Information containing the interface records
    """
    # Create a new database session
    db: Session = SessionLocal()
    try:
        # Get user account
        try:
            account = get_user_using_api_key(api_key)
            # account = get_user_using_api_key(api_key)
            user_id = account.user_id
            time_offset = account.time_offset
            if time_offset == None:
                time_offset = 0
        except Exception as error:
            print(error)
            message = "Failed to get user info. Try to login again. "+str(error)
            return utilities.failedMessage(message)
        
        # interface = db.query(Interface).filter(Interface.interface_url == interface_url).first()
        interface_url_with_slash = "/"+interface_url
        interface = db.query(Interface).filter(or_(Interface.interface_url == interface_url, Interface.interface_url == interface_url_with_slash)).first()
        if interface == None:
            message = "Interface not found."
            return utilities.failedMessage(message)
        
        table_name = interface.table_name
        fields = interface.fields

        interface_columns = {}
        for field in fields:
            if field.get("field_type") in allowed_field_types:
                interface_columns[field.get("field_name")] = field.get("field_type")
            else:
                message = "Failed to validate the data type for: " +str(field.field_name)
                return utilities.failedMessage(message)
            
        # Create a dynamic table object based on the request
        try:
            DynamicTable = create_dynamic_table(table_name, interface_columns, True)
        except Exception as error:
            db.rollback()
            message = "Failed to create table: " +str(error)
            return utilities.failedMessage(message)
        
        try:
            # Query the dynamic table to retrieve data
            # table_data = db.query(DynamicTable).limit(600).all()
            from sqlalchemy import desc
            table_data = db.query(DynamicTable).order_by(desc(DynamicTable.epoch_time)).limit(600).all()
            data = []
            for row in table_data:
                data.append({column.name: getattr(row, column.name) for column in DynamicTable.__table__.columns})
            db.close()

            for record in data:
                epoch_time = record["epoch_time"] + time_offset * 60  # Apply offset
                datetime_time = datetime.datetime.fromtimestamp(epoch_time)
                record["epoch_time"] = datetime_time
            data = sorted(data, key=lambda x: x["epoch_time"])
            return utilities.successMessage(data)
        except Exception as e:
            db.rollback()
            db.close()
            return {"error": str(e)}
    finally:
        db.close()
    

@router.post("/dynamic/interface/{interface_url}", tags=['Dynamic Endpoint'])
async def update_interface(request: Request, interface_url: str):
    """Function used to add a new interface record

    Parameters
    ----------
    interface_url : str
        The interface url that was created in the add method

    Returns
    -------
    dict
        Update status
    """
    # Create a new database session
    db: Session = SessionLocal()
    try:
        db.rollback()
        current_epoch_time = int(time.time())
        interface_url_with_slash = "/"+interface_url
        interface = db.query(Interface).filter(or_(Interface.interface_url == interface_url, Interface.interface_url == interface_url_with_slash)).first()
        if interface == None:
            message = "Interface not found."
            return utilities.failedMessage(message)
        
        table_name = interface.table_name
        interface_owner = interface.interface_owner
        fields = interface.fields
        try:
            payload = await request.body()
            json_payload = json.loads(payload)
            interface_columns = {}
        except Exception as error:
            message = "Failed to get payload. Ensure that the payload is a correct object. Details: " +str(error)
            return utilities.failedMessage(message)
            
        for field in fields:
            if field.get("field_type") in allowed_field_types:
                interface_columns[field.get("field_name")] = field.get("field_type")
            else:
                message = "Failed to validate the data type for: " +str(field.field_name)
                return utilities.failedMessage(message)
            
        # Create a dynamic table object based on the request
        try:
            DynamicTable = create_dynamic_table(table_name, interface_columns, True)
        except Exception as error:
            message = "Failed to create table: " +str(error)
            return utilities.failedMessage(message)
        
        new_row = DynamicTable()

        # We iterate on the template fields and get each column from the payload
        payload_has_epoch_time = False
        for field in fields:
            field_name = field.get("field_name")
            new_field_value = json_payload.get(field_name)
            if new_field_value != None:
                setattr(new_row, field_name, new_field_value)
            elif field.get("required") == True or field.get("required") == "true":
                message = "Failed to update interface. Missing required field: " +str(field_name)
                return utilities.failedMessage(message)
            
        # Check if payload has epoch time. If not, then we set the time to current epoch time
        if new_row.epoch_time == None:
            new_row.epoch_time = current_epoch_time
        
        try:
            db.add(new_row)
            db.commit()
            db.refresh(new_row)

            interface.last_modified = current_epoch_time
            db.add(interface)
            db.commit()
            db.refresh(interface)

            message = "success"
            utilities.increment_user_api_calls(interface_owner)
            return utilities.successMessage(message)
        except Exception as error:
            db.rollback()
            message = "Failed add new interface row: " +str(error)
            return utilities.failedMessage(message)
        
        return {"payload": json.loads(payload), "db": fields}
    finally:
        db.close()
