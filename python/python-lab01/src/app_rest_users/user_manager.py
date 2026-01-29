from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="User Management Service")

class Item(BaseModel):
    name: str
    description: str | None = None

@app.get("/")
def read_root():
    print("Responding to: /")
    return {"message": "Hello from User Management Service!"}

@app.post("/items/")
def create_item(item: Item):
    print(f"Responding to: /items/ : {item}")
    return {"item_name": item.name, "status": "created"}

# CRITICAL for Kubernetes: Health Check Endpoints
@app.get("/healthz")
def health_check():
    """Liveness probe endpoint."""
    return {"status": "healthy"}

@app.get("/ready")
def readiness_check():
    """Readiness probe endpoint."""
    return {"status": "ready"}
