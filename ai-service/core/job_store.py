import json, os, threading

class JobStore:
    def __init__(self, path="job_store.json"):
        self.path = path
        self.lock = threading.Lock()
        if not os.path.exists(path):
            with open(path, "w") as f:
                json.dump({}, f)

    def get(self, job_id):
        with self.lock:
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    return json.load(f).get(job_id)
            except FileNotFoundError:
                return None

    def set(self, job_id, value):
        with self.lock:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data[job_id] = value
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

    def update(self, job_id, **kwargs):
        with self.lock:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if job_id in data:
                data[job_id].update(kwargs)
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
