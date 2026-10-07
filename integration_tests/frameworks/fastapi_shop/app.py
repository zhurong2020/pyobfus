"""HTTP layer. Run with: uvicorn app:app"""

from fastapi import FastAPI, Query

from models import OrderQuote, OrderRequest
from pricing import margin_ratio, quote_order

app = FastAPI(title="Quote service")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/quote", response_model=OrderQuote)
def create_quote(order: OrderRequest) -> OrderQuote:
    return quote_order(order)


@app.get("/margin")
def margin(revenue: float = Query(...), cost: float = Query(...)) -> dict:
    return {"margin": margin_ratio(revenue, cost)}
