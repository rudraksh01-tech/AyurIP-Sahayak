from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AyurIP Sahayak API",
    description="AI-powered Ayurveda IP research assistant",
    version="1.0.0",
)

# React frontend ko backend se connect karne ki permission
app.add_middleware(
    CORSMiddleware,
  allow_origins=[
    "http://localhost:5173",
    "http://localhost:5174",
],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "AyurIP Sahayak API is running!"
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy"
    }