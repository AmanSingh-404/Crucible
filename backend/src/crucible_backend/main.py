from fastapi import FastAPI

app = FastAPI(title="CRUCIBLE API")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
