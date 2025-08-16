import os
import random
from fastapi import FastAPI, Request, Form, Body, APIRouter, Security, HTTPException, Depends
from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader, select_autoescape
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Depends, Body, Request, File, UploadFile, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.security.api_key import APIKeyQuery, APIKeyCookie, APIKeyHeader, APIKey
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.status import HTTP_403_FORBIDDEN
from pydantic import BaseModel
from auth import GetApiKey

import uvicorn

import time
from utils import Utilities
from dbUtils import DbUtils
from handlers.profile import profile
from handlers.dynamic import dynamic
import auth
from database import SessionLocal
db = SessionLocal()

description = """
**Welcome to Dynamic RESTful API Documentation**

---

### 📘 Introduction

The application provides a JSON-based dynamic API for performing operations like adding, retrieving, and modifying data securely.

**Benefits of using the API:**

- 🔐 Built on JSON over HTTPS — accessible and secure from any platform.
- 🐳 Docker-compatible for secure local deployments.
- 🔁 Enables **insert, update, select, and delete** actions on endpoints data.
- 👥 Endpoints are linked to user accounts.
- ⏱️ All timestamps use **epoch time (seconds)**. Some API calls auto-generate these.

---

### 🔐 Security

- All connections use **HTTPS**.
- Authentication via user credentials + access token.
- Use the token provided after login for all subsequent requests.

---

### 🌍 API Servers

- `http://hostname/interface` — Local Server
"""
tags_metadata = [
    {
        "name": "Authentication",
        "description": "Token-based authentication and authorization endpoints.",
    }
]
app = FastAPI(
    title="Dynamic RESTful API",
    description=description,
    version="2.4.1",
    openapi_version="3.1.0",  # Explicitly set the OpenAPI version
    root_path="/interface",
    openapi_tags=tags_metadata,
)

# Get base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Define static and template directories
STATIC_DIR = os.path.join(BASE_DIR, 'static')
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Set up Jinja2 templates
templates = Jinja2Templates(directory=TEMPLATE_DIR)

# Ensure Jinja2 environment consistency
env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=select_autoescape(['html', 'xml'])
)

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(dynamic.router)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

dbUtils = DbUtils()
utilities = Utilities()

oauth_scheme = OAuth2PasswordBearer(tokenUrl="token")


@app.get("/")
async def root():
    return {"message": "Welcome to the FastAPI + MQTT example"}

#=============================================================================================#
@app.get("/version")
def version():
    data = {
        "version": "2.4.1",
        "release_date": "15 July 2025 - 11:28"
    }
    return utilities.successMessage(data)

@app.get("/home")
def home(api_key: APIKey = Depends(GetApiKey)):
    messsage = "If you are seeing this message it means you have logged in"
    return utilities.successMessage(messsage)

@app.get("/test")
def home():
    current_epoch_time = int(time.time())
    data = {
        "message":"You have been Spoiled", 
        "time": current_epoch_time
    }
    return utilities.successMessage(data)

 #==============================================================================#
@app.get("/")
def form_post(request: Request):
    return templates.TemplateResponse('index.html', context={'request': request, 'message': "message"})

if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8888, reload=True)
