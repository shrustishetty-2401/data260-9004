from contextlib import asynccontextmanager

from fastapi import FastAPI

from hw8_client import KafkaVulnerabilityClient


client = KafkaVulnerabilityClient()


@asynccontextmanager
async def lifespan(app):
    await client.start()
    yield
    await client.stop()


app = FastAPI(
    title="DATA-260 HW8 Kafka Vulnerability API",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "hw8-kafka-api",
    }


@app.post("/vulnerabilities")
async def vulnerability_operation(payload: dict):
    operation = payload.get("operation")
    data = payload.get("data", {})

    return await client.request(operation, data)
