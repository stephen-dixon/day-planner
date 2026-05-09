from fastapi import FastAPI

app = FastAPI(title="Day Planner")

@app.get("/health")
def health():
    return {"status": "ok"}
