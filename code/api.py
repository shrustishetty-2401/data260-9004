from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth_db_router import router as auth_router
from benchmark_router import router as benchmark_router
from document_router import router as document_router
from mongo_database import ensure_mongo_setup
from memory_router import router as memory_router
from report_db_router import (
    package_router,
    router as report_router,
)


app = FastAPI(
    title="Open-Source Vulnerability Reports",
    version="5.0.0",
)


app.add_middleware(
    CORSMiddleware,
   allow_origins=[
    "http://localhost:5173",
    "http://localhost:9191",
],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(report_router)
app.include_router(package_router)
app.include_router(benchmark_router)
app.include_router(document_router)
app.include_router(memory_router)

@app.on_event("startup")
def startup_mongo_setup():
    ensure_mongo_setup()

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "hw5-api",
    }
