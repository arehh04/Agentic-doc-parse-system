from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import tempfile
import os

# Import our agents
from agents.orchestrator import OrchestratorAgent
from agents.analytics_agent import AnalyticsAgent

app = FastAPI(title="Carrera AI - Agentic Document Intelligence API")

# Enable CORS for the SvelteKit frontend (which will likely run on localhost:5173 or Vercel domain)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to your Vercel URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Agents
orchestrator = OrchestratorAgent()
analytics_agent = AnalyticsAgent()

class ChatRequest(BaseModel):
    query: str

@app.get("/")
def read_root():
    return {"status": "Carrera AI Backend is running 🏎️"}

@app.post("/api/upload")
async def upload_receipt(file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".jpg", ".jpeg", ".png")):
        raise HTTPException(status_code=400, detail="Only JPG and PNG images are supported.")
        
    try:
        # Save uploaded file to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
            
        # Process using Orchestrator
        state = orchestrator.process_file(tmp_path, file.filename)
        
        # Cleanup
        try:
            os.remove(tmp_path)
        except:
            pass
            
        if not state.is_success:
            raise HTTPException(status_code=500, detail=state.error_message)
            
        return {
            "status": "success",
            "data": state.validated_data.model_dump() if state.validated_data else None,
            "quality_report": state.quality_report
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat_with_database(request: ChatRequest):
    try:
        response = analytics_agent.answer_query(request.query)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
