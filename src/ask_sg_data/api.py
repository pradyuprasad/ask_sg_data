from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

app = FastAPI(
   title="AskSGData",
   description="Natural language queries for Singapore public data",
   version="0.1.0"
)

class Question(BaseModel):
   question: str

class Response(BaseModel):
   text_response: str
   visualization_data: Optional[Dict[str, Any]] = None
   sources: list[str]

@app.get("/health")
async def health_check():
   return {"status": "ok"}

@app.post("/ask", response_model=Response)
async def ask_question(query: Question):
   try:
       # Placeholder for actual implementation
       return {
           "text_response": f"Processed question: {query.question}",
           "visualization_data": None,
           "sources": ["data.gov.sg"]
       }
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))
