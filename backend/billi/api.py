"""FastAPI starter endpoints for BILLI R-20. No AI provider is configured."""
from fastapi import FastAPI
from pydantic import BaseModel, Field
from .intent import classify

app = FastAPI(title="BILLI R-20 API", version="0.1.0", description="Local starter API; deterministic demo routing only.")

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)

class ChatResponse(BaseModel):
    intent: str
    confidence: float
    response: str
    provider: str = "demo-router"

@app.get("/health")
def health():
    return {"status": "ok", "ai_provider": "not_configured", "database": "not_configured"}

@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest):
    intent = classify(payload.message)
    replies = {
        "greeting": "Hello! BILLI R-20 starter backend is online. This is a deterministic demo, not an LLM.",
        "help": "I can route greetings, help, status, and knowledge-search intents. An AI provider and RAG database are not configured yet.",
        "knowledge_search": "Knowledge search is recognized, but no knowledge database is connected yet.",
        "status": "API is running. AI provider and knowledge database are not configured.",
        "unknown": "I received your message, but no configured intent matched. Connect a model provider in a future phase for open-ended answers.",
    }
    return ChatResponse(intent=intent.name, confidence=intent.confidence, response=replies[intent.name])
