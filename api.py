import os, json, uuid
from fastapi import FastAPI
from upstash_redis import Redis

app = FastAPI()

redis = Redis(
    url=os.getenv("UPSTASH_REDIS_REST_URL"),
    token=os.getenv("UPSTASH_REDIS_REST_TOKEN"),
)

QUEUE_KEY = "jobs:queue"

@app.post("/enqueue")
def enqueue(system: str, user: str, model: str = "gpt-4.1"):
    job_id = str(uuid.uuid4())
    redis.set(f"job:{job_id}:status", "queued")
    redis.set(f"job:{job_id}:payload", json.dumps({"system": system, "user": user, "model": model}))
    redis.rpush(QUEUE_KEY, job_id)
    return {"job_id": job_id}

@app.get("/status/{job_id}")
def status(job_id: str):
    s = redis.get(f"job:{job_id}:status") or "unknown"
    return {"status": s}

@app.get("/result/{job_id}")
def result(job_id: str):
    r = redis.get(f"job:{job_id}:result")
    if r is None:
        return {"ready": False}
    return {"ready": True, "result": r}
