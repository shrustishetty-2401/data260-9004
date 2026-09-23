from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth_db_router import router as auth_router
from benchmark_router import router as benchmark_router
from report_db_router import router as report_router

app = FastAPI(
    title="Open-Source Vulnerability Reports",
    version="4.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(report_router)
app.include_router(benchmark_router)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "hw4-api",
    }