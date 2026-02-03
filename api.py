import requests
import time
import os, json, uuid
from fastapi import FastAPI, BackgroundTasks
from upstash_redis import Redis
from tasks import run_draft

app = FastAPI()

redis = Redis(
    url=os.getenv("UPSTASH_REDIS_REST_URL"),
    token=os.getenv("UPSTASH_REDIS_REST_TOKEN"),
)

def process_job(job_id: str):
    status_key = f"job:{job_id}:status"
    payload_key = f"job:{job_id}:payload"
    result_key = f"job:{job_id}:result"

    redis.set(status_key, "started")

    payload = redis.get(payload_key)
    payload = payload if isinstance(payload, str) else payload.decode("utf-8")
    data = json.loads(payload)

    try:
        output = run_draft(data["system"], data["user"], data.get("model", "gpt-4.1"))
        redis.set(result_key, output)
        redis.set(status_key, "finished")
    except Exception as e:
        redis.set(result_key, str(e))
        redis.set(status_key, "failed")

@app.post("/enqueue")
def enqueue(system: str, user: str, model: str = "gpt-4.1", background_tasks: BackgroundTasks = None):
    job_id = str(uuid.uuid4())
    redis.set(f"job:{job_id}:status", "queued")
    redis.set(f"job:{job_id}:payload", json.dumps({"system": system, "user": user, "model": model}))

    background_tasks.add_task(process_job, job_id)

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
