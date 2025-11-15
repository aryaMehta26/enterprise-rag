import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from app.rag import answer_query
from app.auth import OAuth2PasswordRequestForm, authenticate_user, create_access_token, get_current_user

load_dotenv()

app = FastAPI()

# CORS (adjust origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static frontend (React-lite)
if os.path.isdir("web"):
    app.mount("/web", StaticFiles(directory="web", html=True), name="web")

class QueryRequest(BaseModel):
    question: str
    source: str = "all"  # 'all', 'PDF', or 'Wikipedia'

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/auth/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    token = create_access_token(user["username"], user["role"])
    return {"access_token": token, "token_type": "bearer"}

@app.post("/query")
def query_endpoint(request: QueryRequest, user=Depends(get_current_user)):
    try:
        result = answer_query(request.question, request.source)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 