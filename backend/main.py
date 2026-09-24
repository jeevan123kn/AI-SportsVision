from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from routes import players, upload, analysis, history, prediction, coaching, comparison
from database.database import init_db

load_dotenv()

app = FastAPI(title="AI SportsVision API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(players.router)
app.include_router(upload.router)
app.include_router(analysis.router)
app.include_router(history.router)
app.include_router(prediction.router)
app.include_router(coaching.router)
app.include_router(comparison.router)


@app.on_event("startup")
def startup_event():
    init_db()


@app.get("/")
def read_root():
    return {"message": "AI SportsVision backend is running"}
