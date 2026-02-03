import os
import time
import json
from upstash_redis import Redis
from tasks import run_draft

redis = Redis(
    url=os.getenv("UPSTASH_REDIS_REST_URL"),
    token=os.getenv("UPSTASH_REDIS_REST_TOKEN"),
)

QUEUE_KEY = "jobs:queue"

def main():
    while True:
        job_id = redis.lpop(QUEUE_KEY)
        if not job_id:
            time.sleep(1)
            continue

        job_id = job_id if isinstance(job_id, str) else job_id.decode("utf-8")

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

if __name__ == "__main__":
    main()
