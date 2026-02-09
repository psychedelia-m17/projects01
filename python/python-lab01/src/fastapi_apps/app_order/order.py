from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Order Management API")

# Data Model
class Order(BaseModel):
    id: int
    item: str
    quantity: int
    price: float

# In-memory database
orders_db = []

@app.get("/orders", response_model=List[Order])
async def get_orders():
    return orders_db

@app.get("/orders/{order_id}", response_model=Order)
async def get_order(order_id: int):
    order = next((o for o in orders_db if o.id == order_id), None)
    if not order:
        raise HTTPException(status_status=404, detail="Order not found")
    return order

@app.post("/orders", response_model=Order)
async def create_order(order: Order):
    if any(o.id == order.id for o in orders_db):
        raise HTTPException(status_code=400, detail="Order ID already exists")
    orders_db.append(order)
    return order

@app.put("/orders/{order_id}", response_model=Order)
async def update_order(order_id: int, updated_order: Order):
    idx = next((i for i, o in enumerate(orders_db) if o.id == order_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Order not found")
    orders_db[idx] = updated_order
    return updated_order

@app.delete("/orders/{order_id}")
async def delete_order(order_id: int):
    global orders_db
    orders_db = [o for o in orders_db if o.id != order_id]
    return {"message": "Order deleted successfully"}
